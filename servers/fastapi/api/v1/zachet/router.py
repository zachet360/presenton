"""
zachet.ai integration endpoints.

Isolated from the main presenton codebase to minimise merge conflicts
when pulling upstream updates.
"""

import asyncio
from datetime import datetime
import json
import math
import os
import random
import traceback
from typing import List, Optional
import uuid

import aiohttp
import dirtyjson
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from constants.presentation import DEFAULT_TEMPLATES
from models.presentation_outline_model import SlideOutlineModel
from models.presentation_structure_model import PresentationStructureModel
from models.sql.async_presentation_generation_status import (
    AsyncPresentationGenerationTaskModel,
)
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from services.documents_loader import DocumentsLoader
from services.image_generation_service import ImageGenerationService
from services.temp_file_service import TEMP_FILE_SERVICE
from utils.asset_directory_utils import get_images_directory
from utils.export_utils import export_presentation
from utils.get_layout_by_name import get_layout_by_name
from api.v1.zachet.generate_outlines import (
    generate_zachet_outlines,
    ZachetPresentationOutlineModel,
)
from api.v1.zachet.generate_image_prompt import generate_image_prompt
from utils.llm_calls.generate_presentation_structure import (
    generate_presentation_structure,
)
from utils.llm_calls.generate_slide_content import (
    get_slide_content_from_type_and_outline,
)
from utils.ppt_utils import (
    get_presentation_title_from_outlines,
    select_toc_or_list_slide_layout_index,
)
from utils.process_slides import process_slide_and_fetch_assets


ZACHET_ROUTER = APIRouter(prefix="/presentation", tags=["Zachet Integration"])


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


async def _send_callback(callback_url: str, payload: dict):
    """Fire-and-forget POST to the caller's webhook URL."""
    try:
        async with aiohttp.ClientSession() as session:
            webhook_secret = os.getenv("WEBHOOK_SECRET")
            headers = {"Content-Type": "application/json"}
            if webhook_secret:
                headers["Authorization"] = f"Bearer {webhook_secret}"
            async with session.post(
                callback_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                print(f"Callback to {callback_url}: status={resp.status}")
    except Exception as e:
        print(f"Callback error to {callback_url}: {e}")


async def _refine_image_prompts(
    slides: List[SlideModel],
    outlines: ZachetPresentationOutlineModel,
    document_summary: str,
):
    """Replace __image_prompt__ in each slide with an LLM-optimised search query."""
    from utils.dict_utils import get_dict_paths_with_key, get_dict_at_path

    tasks = []
    task_targets = []  # (slide_index, image_dict) for each task

    for i, slide in enumerate(slides):
        image_paths = get_dict_paths_with_key(slide.content, "__image_prompt__")
        if not image_paths:
            continue

        outline = outlines.slides[i] if i < len(outlines.slides) else None
        excerpt = getattr(outline, "source_excerpt", "") if outline else ""

        for path in image_paths:
            image_dict = get_dict_at_path(slide.content, path)
            image_type = image_dict.get("__image_type__", "photo")
            tasks.append(
                generate_image_prompt(
                    slide_content=slide.content,
                    image_type=image_type,
                    source_excerpt=excerpt,
                    document_summary=document_summary,
                )
            )
            task_targets.append(image_dict)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for image_dict, result in zip(task_targets, results):
        if isinstance(result, str) and result.strip():
            image_dict["__image_prompt__"] = result
        # on error — keep the original __image_prompt__ from LLM #3


# ──────────────────────────────────────────────────────────────
# Background task
# ──────────────────────────────────────────────────────────────


async def _generate_from_document_task(
    presentation_id: uuid.UUID,
    file_path: str,
    callback_url: Optional[str],
    metadata: dict,
    sql_session: AsyncSession,
):
    """Background task: extract text from .docx, generate presentation, call webhook."""
    work_id = metadata.get("work_id", "")
    try:
        # Update status to processing
        async_status = await sql_session.get(
            AsyncPresentationGenerationTaskModel, f"doc-{presentation_id}"
        )
        if async_status:
            async_status.status = "processing"
            async_status.message = "Extracting document text"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # 1. Extract text from document
        documents_loader = DocumentsLoader(file_paths=[file_path])
        await documents_loader.load_documents()
        documents = documents_loader.documents
        document_text = "\n\n".join(documents) if documents else ""

        if not document_text.strip():
            raise Exception("Could not extract text from the uploaded document")

        topic = metadata.get("topic", "")
        work_type = metadata.get("work_type", "essay")
        n_slides = metadata.get("n_slides", 10)
        language = metadata.get("language", "Russian")
        include_title_slide = metadata.get("include_title_slide", True)
        include_toc = metadata.get("include_toc_slide", False)
        tone = metadata.get("tone", "educational")
        template = random.choice(DEFAULT_TEMPLATES)

        # Build content prompt from document
        content = f"Topic: {topic}\nWork type: {work_type}\n\nDocument content:\n{document_text}"

        # 2. Generate outlines (with source_excerpt per slide)
        if async_status:
            async_status.message = "Generating presentation outlines"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        n_slides_to_generate = n_slides
        if include_toc:
            needed_toc_count = math.ceil(
                ((n_slides - 1) if include_title_slide else n_slides) / 10
            )
            n_slides_to_generate -= math.ceil(
                (n_slides - needed_toc_count) / 10
            )

        presentation_outlines_text = ""
        async for chunk in generate_zachet_outlines(
            content,
            n_slides_to_generate,
            language,
            "",  # additional_context already in content
            tone,
            "standard",
            None,  # instructions
            include_title_slide,
        ):
            if isinstance(chunk, HTTPException):
                raise chunk
            presentation_outlines_text += chunk

        try:
            presentation_outlines_json = dict(
                dirtyjson.loads(presentation_outlines_text)
            )
        except Exception:
            raise Exception("Failed to parse presentation outlines from LLM")

        presentation_outlines = ZachetPresentationOutlineModel(**presentation_outlines_json)
        total_outlines = n_slides_to_generate

        # 3. Select layout and structure
        if async_status:
            async_status.message = "Selecting layout for each slide"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        layout_model = await get_layout_by_name(template)
        total_slide_layouts = len(layout_model.slides)

        if layout_model.ordered:
            presentation_structure = layout_model.to_presentation_structure()
        else:
            presentation_structure = await generate_presentation_structure(
                presentation_outlines,
                layout_model,
                None,
                False,
            )

        presentation_structure.slides = presentation_structure.slides[:total_outlines]
        for index in range(total_outlines):
            random_slide_index = random.randint(0, total_slide_layouts - 1)
            if index >= total_outlines:
                presentation_structure.slides.append(random_slide_index)
                continue
            if presentation_structure.slides[index] >= total_slide_layouts:
                presentation_structure.slides[index] = random_slide_index

        # Handle TOC
        if include_toc:
            n_toc_slides = n_slides - total_outlines
            toc_slide_layout_index = select_toc_or_list_slide_layout_index(layout_model)
            if toc_slide_layout_index != -1:
                outline_index = 1 if include_title_slide else 0
                for i in range(n_toc_slides):
                    outlines_to = outline_index + 10
                    if total_outlines == outlines_to:
                        outlines_to -= 1
                    presentation_structure.slides.insert(
                        i + 1 if include_title_slide else i,
                        toc_slide_layout_index,
                    )
                    toc_outline = "Table of Contents\n\n"
                    for outline in presentation_outlines.slides[outline_index:outlines_to]:
                        page_number = (
                            outline_index - i + n_toc_slides + 1
                            if include_title_slide
                            else outline_index - i + n_toc_slides
                        )
                        toc_outline += f"Slide page number: {page_number}\n Slide Content: {outline.content[:100]}\n\n"
                        outline_index += 1
                    outline_index += 1
                    presentation_outlines.slides.insert(
                        i + 1 if include_title_slide else i,
                        SlideOutlineModel(content=toc_outline),
                    )

        # 4. Create presentation model
        presentation = PresentationModel(
            id=presentation_id,
            content=content[:2000],
            n_slides=n_slides,
            language=language,
            title=topic or get_presentation_title_from_outlines(presentation_outlines),
            outlines=presentation_outlines.model_dump(),
            layout=layout_model.model_dump(),
            structure=presentation_structure.model_dump(),
            tone=tone,
            verbosity="standard",
            instructions=None,
        )

        # 5. Generate slides
        if async_status:
            async_status.message = "Generating slides"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        image_generation_service = ImageGenerationService(get_images_directory())
        slides: List[SlideModel] = []
        generated_assets = []

        slide_layout_indices = presentation_structure.slides
        slide_layouts = [layout_model.slides[idx] for idx in slide_layout_indices]

        # Build per-slide presentation context from summary + source_excerpt
        document_summary = getattr(presentation_outlines, "summary", "") or ""

        def _slide_context(i: int) -> str:
            slide_outline = presentation_outlines.slides[i]
            excerpt = getattr(slide_outline, "source_excerpt", "") or ""
            return (
                f"Presentation topic: {topic}\n"
                f"Work type: {work_type}\n"
                f"Document summary:\n{document_summary}\n\n"
                f"Source document excerpt for this slide:\n{excerpt}"
            )

        batch_size = 10
        for start in range(0, len(slide_layouts), batch_size):
            end = min(start + batch_size, len(slide_layouts))
            content_tasks = [
                get_slide_content_from_type_and_outline(
                    slide_layouts[i],
                    presentation_outlines.slides[i],
                    language,
                    tone,
                    "standard",
                    None,
                    _slide_context(i),
                )
                for i in range(start, end)
            ]
            batch_contents = await asyncio.gather(*content_tasks)

            for offset, slide_content in enumerate(batch_contents):
                i = start + offset
                slide = SlideModel(
                    presentation=presentation_id,
                    layout_group=layout_model.name,
                    layout=slide_layouts[i].id,
                    index=i,
                    speaker_note=slide_content.get("__speaker_note__"),
                    content=slide_content,
                )
                slides.append(slide)

        # 5.1. Regenerate image prompts with full slide context (LLM #4)
        if async_status:
            async_status.message = "Optimising image search queries"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        await _refine_image_prompts(slides, presentation_outlines, document_summary)

        if async_status:
            async_status.message = "Fetching assets for slides"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # Fetch assets sequentially to avoid rate limits
        for slide in slides:
            assets = await process_slide_and_fetch_assets(image_generation_service, slide)
            generated_assets.extend(assets)

        # 6. Save to DB
        sql_session.add(presentation)
        sql_session.add_all(slides)
        sql_session.add_all(generated_assets)
        await sql_session.commit()

        # 7. Export PPTX
        if async_status:
            async_status.message = "Exporting presentation"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        presentation_and_path = await export_presentation(
            presentation_id, presentation.title or str(uuid.uuid4()), "pptx"
        )

        # 8. Mark completed
        if async_status:
            async_status.status = "completed"
            async_status.message = "Presentation generation completed"
            async_status.data = {
                "presentation_id": str(presentation_id),
                "path": presentation_and_path.path,
            }
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # 9. Fire callback webhook
        if callback_url:
            await _send_callback(callback_url, {
                "presentation_id": str(presentation_id),
                "work_id": work_id,
                "status": "completed",
                "download_url": f"/api/v1/ppt/presentation/{presentation_id}/export/pptx",
                "error": None,
            })

    except Exception as e:
        traceback.print_exc()
        error_msg = str(e) if str(e) else "Presentation generation failed"

        # Update async status
        try:
            async_status = await sql_session.get(
                AsyncPresentationGenerationTaskModel, f"doc-{presentation_id}"
            )
            if async_status:
                async_status.status = "failed"
                async_status.message = error_msg
                async_status.error = {"detail": error_msg}
                async_status.updated_at = datetime.now()
                sql_session.add(async_status)
                await sql_session.commit()
        except Exception:
            pass

        # Fire failure callback
        if callback_url:
            await _send_callback(callback_url, {
                "presentation_id": str(presentation_id),
                "work_id": work_id,
                "status": "failed",
                "download_url": None,
                "error": error_msg,
            })


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@ZACHET_ROUTER.post("/generate-from-document")
async def generate_presentation_from_document(
    file: UploadFile = File(...),
    callback_url: Optional[str] = Form(None),
    metadata: str = Form("{}"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Generate a presentation from an uploaded .docx file.

    Accepts multipart/form-data with:
    - file: .docx file
    - callback_url: URL to POST webhook when done
    - metadata: JSON string with work_id, work_type, topic, n_slides, language, etc.

    Returns immediately with presentation_id and status="processing".
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith((".docx", ".doc", ".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Only .docx, .doc, .pdf, and .txt files are supported",
        )

    # Parse metadata
    try:
        meta = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    # Save uploaded file to temp directory
    temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    presentation_id = uuid.uuid4()

    # Create async task record for status tracking
    async_status = AsyncPresentationGenerationTaskModel(
        id=f"doc-{presentation_id}",
        status="processing",
        message="Queued for generation",
        data={"presentation_id": str(presentation_id), "work_id": meta.get("work_id", "")},
    )
    sql_session.add(async_status)
    await sql_session.commit()

    # Run generation in background
    background_tasks.add_task(
        _generate_from_document_task,
        presentation_id,
        file_path,
        callback_url,
        meta,
        sql_session,
    )

    return {
        "presentation_id": str(presentation_id),
        "status": "processing",
    }


@ZACHET_ROUTER.get("/{id}/status")
async def get_presentation_generation_status(
    id: uuid.UUID,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Get status of a presentation generation task (for polling fallback).

    Checks the async task record keyed by doc-{presentation_id}.
    If no async task exists, checks if the presentation itself exists (completed via sync flow).
    """
    # Check async task record first
    task_id = f"doc-{id}"
    async_status = await sql_session.get(AsyncPresentationGenerationTaskModel, task_id)
    if async_status:
        progress = 0
        if async_status.status == "completed":
            progress = 100
        elif async_status.status == "failed":
            progress = 0
        elif async_status.message:
            # Rough progress estimation based on message
            stage_progress = {
                "Queued for generation": 5,
                "Extracting document text": 10,
                "Generating presentation outlines": 25,
                "Selecting layout for each slide": 40,
                "Generating slides": 60,
                "Fetching assets for slides": 80,
                "Exporting presentation": 90,
                "Presentation generation completed": 100,
            }
            progress = stage_progress.get(async_status.message, 50)

        return {
            "status": async_status.status,
            "progress": progress,
            "message": async_status.message,
        }

    # Check if presentation exists (might have been created via another flow)
    presentation = await sql_session.get(PresentationModel, id)
    if presentation:
        return {"status": "completed", "progress": 100, "message": "Presentation ready"}

    raise HTTPException(status_code=404, detail="Presentation not found")


@ZACHET_ROUTER.get("/{id}/export/pptx")
async def export_presentation_by_id_pptx(
    id: uuid.UUID,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Export and download a presentation as PPTX by its ID."""
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_and_path = await export_presentation(
        id, presentation.title or str(uuid.uuid4()), "pptx"
    )

    file_path = presentation_and_path.path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"{presentation.title or 'presentation'}.pptx",
    )


@ZACHET_ROUTER.get("/{id}/export/pdf")
async def export_presentation_by_id_pdf(
    id: uuid.UUID,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Export and download a presentation as PDF by its ID."""
    presentation = await sql_session.get(PresentationModel, id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    presentation_and_path = await export_presentation(
        id, presentation.title or str(uuid.uuid4()), "pdf"
    )

    file_path = presentation_and_path.path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{presentation.title or 'presentation'}.pdf",
    )
