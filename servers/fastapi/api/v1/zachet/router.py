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
from api.v1.zachet.generation_logger import GenerationLogger
from models.sql.generation_log import GenerationLogModel


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

    SKIP_LAYOUTS = set()  # refine all slides including title

    for i, slide in enumerate(slides):
        # Skip slides with manually crafted prompts
        if slide.layout in SKIP_LAYOUTS:
            continue

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


def _clamp_illustration_count(slides: List[SlideModel], target: int = 1):
    """Ensure exactly `target` non-metrics slides use __image_type__='illustration'.

    Skips title, closing, and metrics slides (metrics always use illustration).
    """
    from utils.dict_utils import get_dict_paths_with_key, get_dict_at_path

    SKIP_LAYOUTS = {"zachet:zachet-title-slide"}
    illustration_dicts: list = []
    photo_dicts: list = []

    eligible_slides = slides[1:-1] if len(slides) > 2 else slides

    for slide in eligible_slides:
        if slide.layout in SKIP_LAYOUTS:
            continue  # title handled separately
        image_paths = get_dict_paths_with_key(slide.content, "__image_prompt__")
        for path in image_paths:
            image_dict = get_dict_at_path(slide.content, path)
            if image_dict.get("__image_type__") == "illustration":
                illustration_dicts.append(image_dict)
            else:
                photo_dicts.append(image_dict)

    # Too many illustrations — demote extras to photo
    while len(illustration_dicts) > target:
        demoted = illustration_dicts.pop()
        demoted["__image_type__"] = "photo"

    # Too few illustrations — promote from photos
    while len(illustration_dicts) < target and photo_dicts:
        promoted = photo_dicts.pop(0)
        promoted["__image_type__"] = "illustration"
        illustration_dicts.append(promoted)


def _override_title_image_prompt(slides: List[SlideModel]):
    """For the title slide: set a clean search query from the title for Yandex Search."""
    TITLE_LAYOUT = "zachet:zachet-title-slide"

    for slide in slides:
        if slide.layout != TITLE_LAYOUT:
            continue
        img = slide.content.get("image")
        if not isinstance(img, dict):
            continue

        title = slide.content.get("title", "")
        # Clean search query: just the topic, no fluff
        img["__image_prompt__"] = title
        img["__image_type__"] = "photo"




def _set_image_orientation(
    slides: List[SlideModel],
    orientation: str = "IMAGE_ORIENTATION_SQUARE",
):
    """Inject __image_orientation__ into every image dict so Yandex Search
    requests images matching the zachet template container shape."""
    from utils.dict_utils import get_dict_paths_with_key, get_dict_at_path

    for slide in slides:
        image_paths = get_dict_paths_with_key(slide.content, "__image_prompt__")
        for path in image_paths:
            image_dict = get_dict_at_path(slide.content, path)
            image_dict["__image_orientation__"] = orientation


def _make_all_required(schema: dict):
    """Recursively ensure every property in JSON schema is required.

    Zod `.default()` emits properties WITHOUT listing them in `required`,
    so the LLM (with strict=False) may legally omit them → empty slides.
    """
    if not isinstance(schema, dict):
        return
    props = schema.get("properties")
    if isinstance(props, dict):
        schema["required"] = list(props.keys())
        for prop_schema in props.values():
            if isinstance(prop_schema, dict):
                _make_all_required(prop_schema)
    items = schema.get("items")
    if isinstance(items, dict):
        _make_all_required(items)
    for key in ("$defs", "definitions"):
        defs = schema.get(key)
        if isinstance(defs, dict):
            for def_schema in defs.values():
                if isinstance(def_schema, dict):
                    _make_all_required(def_schema)


def _fill_defaults(content: dict, schema: dict) -> dict:
    """Post-process LLM response: fill any missing fields from schema defaults.

    Safety net for truncated JSON (dirtyjson parses partial output) or
    fields the LLM skipped despite being required.
    """
    if not isinstance(content, dict) or not isinstance(schema, dict):
        return content
    properties = schema.get("properties", {})
    for key, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            continue
        if key not in content:
            if "default" in prop_schema:
                content[key] = prop_schema["default"]
            else:
                ptype = prop_schema.get("type")
                if ptype == "string":
                    content[key] = ""
                elif ptype == "array":
                    content[key] = []
                elif ptype == "object":
                    content[key] = {}
        elif isinstance(content[key], dict) and prop_schema.get("type") == "object":
            _fill_defaults(content[key], prop_schema)
        elif isinstance(content[key], list) and prop_schema.get("type") == "array":
            items_schema = prop_schema.get("items", {})
            if isinstance(items_schema, dict) and items_schema.get("type") == "object":
                for item in content[key]:
                    if isinstance(item, dict):
                        _fill_defaults(item, items_schema)
    return content


def _pick_content_layout(outline_text: str, available: List[int]) -> int:
    """Heuristic: choose the best content layout index for an outline.

    available = subset of [4=Bullets, 5=Image, 6=Comparison, 7=Metrics]

    Rules:
      - keywords suggesting comparison/contrast → 6 (Comparison)
      - keywords suggesting numbers/statistics → 7 (Metrics)
      - short outline with many list-like lines → 4 (Bullets)
      - otherwise → 5 (Image)
    """
    BULLETS_IDX, IMAGE_IDX, COMPARISON_IDX, METRICS_IDX = 4, 5, 6, 7
    text = (outline_text or "").lower()

    comparison_kw = [
        "сравн", "против", "отлич", "разниц", "преимущест", "недостат",
        "за и против", "плюс", "минус", "vs", "compar", "versus",
        "differ", "advant", "disadvant",
    ]
    metrics_kw = [
        "метрик", "статистик", "процент", "%", "число", "показател",
        "данны", "рост", "снижен", "увеличен", "уменьшен",
        "metric", "statistic", "percent", "number", "growth", "rate",
        "kpi", "result",
    ]

    if any(kw in text for kw in comparison_kw) and COMPARISON_IDX in available:
        return COMPARISON_IDX
    if any(kw in text for kw in metrics_kw) and METRICS_IDX in available:
        return METRICS_IDX

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    bullet_lines = sum(1 for l in lines if l.startswith(("-", "•", "*", "–")) or (len(l) > 1 and l[0].isdigit() and l[1] in ".)" ))
    if bullet_lines >= 3 and BULLETS_IDX in available:
        return BULLETS_IDX

    if IMAGE_IDX in available:
        return IMAGE_IDX
    return available[0] if available else BULLETS_IDX


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
    log = GenerationLogger(filename=os.path.basename(file_path))
    gen_log_model = GenerationLogModel(
        presentation_id=presentation_id,
        filename=os.path.basename(file_path),
    )
    sql_session.add(gen_log_model)
    await sql_session.commit()

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
        log.begin("Извлечение текста из документа (DocumentsLoader)", file_path=file_path)
        documents_loader = DocumentsLoader(file_paths=[file_path])
        await documents_loader.load_documents()
        documents = documents_loader.documents
        document_text = "\n\n".join(documents) if documents else ""

        if not document_text.strip():
            raise Exception("Could not extract text from the uploaded document")
        log.end(text_length=len(document_text), preview=document_text[:500])

        topic = metadata.get("topic", "")
        work_type = metadata.get("work_type", "essay")
        n_slides = metadata.get("n_slides", 10)
        language = metadata.get("language", "Russian")
        include_title_slide = metadata.get("include_title_slide", True)
        include_toc = metadata.get("include_toc_slide", False)
        tone = metadata.get("tone", "educational")
        template = "zachet"
        is_project = work_type.lower() == "project"

        # For project work type, add 4 structural slides
        if is_project:
            n_slides += 4

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

        log.begin("LLM #1: Генерация outlines (generate_zachet_outlines)", n_slides=n_slides_to_generate, language=language, tone=tone)
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
        total_outlines = len(presentation_outlines.slides)
        log.end(
            outlines_count=len(presentation_outlines.slides),
            summary=getattr(presentation_outlines, "summary", ""),
            outlines=[
                {"content": s.content, "source_excerpt": getattr(s, "source_excerpt", "")}
                for s in presentation_outlines.slides
            ],
        )

        # 3. Select layout and structure
        if async_status:
            async_status.message = "Selecting layout for each slide"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        log.begin("Выбор шаблона и структуры слайдов (get_layout_by_name)", template=template)
        layout_model = await get_layout_by_name(template)
        total_slide_layouts = len(layout_model.slides)

        # Zachet always uses our own cycling logic (ignore layout_model.ordered)
        # Template indices:
        # 0=Title, 1=Goal, 2=Tasks, 3=Problem, 4=Bullets, 5=Image,
        # 6=Comparison, 7=Metrics, 8=Perspectives, 9=Closing
        TITLE_IDX = 0
        GOAL_IDX = 1
        TASKS_IDX = 2
        PROBLEM_IDX = 3
        CONTENT_INDICES = [4, 5, 6, 7]  # Bullets, Image, Comparison, Metrics
        PERSPECTIVES_IDX = 8
        CLOSING_IDX = 9

        slides: List[int] = []
        if is_project:
            # Project: Title → Goal → Tasks → Problem → [content...] → Perspectives → Closing
            slides.append(TITLE_IDX)
            slides.append(GOAL_IDX)
            slides.append(TASKS_IDX)
            slides.append(PROBLEM_IDX)
            content_start = 4  # first content outline index
            content_count = total_outlines - 6  # minus title, goal, tasks, problem, perspectives, closing
            used_counts = {idx: 0 for idx in CONTENT_INDICES}
            for c in range(max(content_count, 0)):
                outline_text = presentation_outlines.slides[content_start + c].content if (content_start + c) < len(presentation_outlines.slides) else ""
                # Prefer layouts not yet used; fall back to all
                min_used = min(used_counts.values()) if used_counts else 0
                prefer = [idx for idx, cnt in used_counts.items() if cnt == min_used]
                chosen = _pick_content_layout(outline_text, prefer if prefer else CONTENT_INDICES)
                used_counts[chosen] = used_counts.get(chosen, 0) + 1
                slides.append(chosen)
            slides.append(PERSPECTIVES_IDX)
            slides.append(CLOSING_IDX)
        else:
            # Default: Title → [content...] → Closing
            slides.append(TITLE_IDX)
            content_start = 1  # first content outline index
            content_count = total_outlines - 2  # minus title, closing
            used_counts = {idx: 0 for idx in CONTENT_INDICES}
            for c in range(max(content_count, 0)):
                outline_text = presentation_outlines.slides[content_start + c].content if (content_start + c) < len(presentation_outlines.slides) else ""
                min_used = min(used_counts.values()) if used_counts else 0
                prefer = [idx for idx, cnt in used_counts.items() if cnt == min_used]
                chosen = _pick_content_layout(outline_text, prefer if prefer else CONTENT_INDICES)
                used_counts[chosen] = used_counts.get(chosen, 0) + 1
                slides.append(chosen)
            slides.append(CLOSING_IDX)

        presentation_structure = PresentationStructureModel(slides=slides)

        log.end(
            ordered=layout_model.ordered,
            total_layouts=total_slide_layouts,
            structure=presentation_structure.slides,
            layout_names=[s.name or s.id for s in layout_model.slides],
        )

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

        log.begin("LLM #3: Генерация контента слайдов (get_slide_content_from_type_and_outline)", total_slides=len(presentation_structure.slides))
        image_generation_service = ImageGenerationService(get_images_directory())
        slides: List[SlideModel] = []
        generated_assets = []

        slide_layout_indices = presentation_structure.slides
        slide_layouts = [layout_model.slides[idx] for idx in slide_layout_indices]

        # FIX: make every property required so LLM cannot skip fields
        for layout in slide_layouts:
            _make_all_required(layout.json_schema)

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
                # FIX: fill any fields the LLM missed (truncated JSON, etc.)
                _fill_defaults(slide_content, slide_layouts[i].json_schema)
                slide = SlideModel(
                    presentation=presentation_id,
                    layout_group=layout_model.name,
                    layout=slide_layouts[i].id,
                    index=i,
                    speaker_note=slide_content.get("__speaker_note__") or "",
                    content=slide_content,
                )
                slides.append(slide)
                log.add_substep("LLM #3: Генерация контента слайдов (get_slide_content_from_type_and_outline)", {
                    "slide_index": i,
                    "layout": slide_layouts[i].id,
                    "content": slide_content,
                })

        log.end(slides_generated=len(slides))

        # 5.0.1 Default missing __image_type__ to "photo"
        for slide in slides:
            img = slide.content.get("image")
            if isinstance(img, dict) and "__image_prompt__" in img and not img.get("__image_type__"):
                img["__image_type__"] = "photo"

        # 5.0.2 Override image prompt for title slide
        _override_title_image_prompt(slides)

        # 5.1. Regenerate image prompts with full slide context (LLM #4)
        if async_status:
            async_status.message = "Optimising image search queries"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        log.begin("LLM #4: Уточнение поисковых запросов для картинок (generate_image_prompt)")
        await _refine_image_prompts(slides, presentation_outlines, document_summary)
        log.end(refined_slides=[
            {"index": i, "image_prompt": s.content.get("image", {}).get("__image_prompt__"), "image_type": s.content.get("image", {}).get("__image_type__")}
            for i, s in enumerate(slides) if isinstance(s.content.get("image"), dict)
        ])

        # 5.2. Clamp to exactly 1 illustration (YandexART infographic)
        log.begin("Выбор слайда для инфографики (_clamp_illustration_count)")
        _clamp_illustration_count(slides)
        log.end(result=[
            {"index": i, "type": s.content.get("image", {}).get("__image_type__")}
            for i, s in enumerate(slides) if isinstance(s.content.get("image"), dict)
        ])

        # 5.3. Remove orientation filter so Yandex returns most relevant images
        _set_image_orientation(slides, orientation="")

        if async_status:
            async_status.message = "Fetching assets for slides"
            async_status.updated_at = datetime.now()
            sql_session.add(async_status)
            await sql_session.commit()

        # Fetch assets sequentially to avoid rate limits
        log.begin("Загрузка картинок и иконок (process_slide_and_fetch_assets → Yandex)")
        for slide in slides:
            assets = await process_slide_and_fetch_assets(image_generation_service, slide)
            generated_assets.extend(assets)
            image_info = slide.content.get("image") if isinstance(slide.content.get("image"), dict) else None
            if image_info:
                log.add_substep("Загрузка картинок и иконок (process_slide_and_fetch_assets → Yandex)", {
                    "slide_index": slide.index,
                    "image_prompt": image_info.get("__image_prompt__"),
                    "image_type": image_info.get("__image_type__"),
                    "image_url": image_info.get("__image_url__"),
                })
        log.end(total_assets=len(generated_assets))

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

        log.begin("Экспорт в PPTX (export_presentation → Puppeteer)")
        presentation_and_path = await export_presentation(
            presentation_id, presentation.title or str(uuid.uuid4()), "pptx"
        )
        log.end(path=presentation_and_path.path)

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

        # Save generation log
        gen_log_model.presentation_id = presentation_id
        gen_log_model.status = "completed"
        gen_log_model.finished_at = datetime.now()
        gen_log_model.total_duration_ms = log.total_duration_ms()
        gen_log_model.steps = log.steps
        sql_session.add(gen_log_model)
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
        log.end_with_error(error_msg)

        # Save generation log on failure
        try:
            gen_log_model.status = "failed"
            gen_log_model.finished_at = datetime.now()
            gen_log_model.total_duration_ms = log.total_duration_ms()
            gen_log_model.steps = log.steps
            gen_log_model.error = error_msg
            sql_session.add(gen_log_model)
            await sql_session.commit()
        except Exception:
            pass

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


@ZACHET_ROUTER.get("/logs")
async def list_generation_logs(
    sql_session: AsyncSession = Depends(get_async_session),
):
    """List all generation logs, newest first."""
    from sqlalchemy import select

    result = await sql_session.execute(
        select(GenerationLogModel).order_by(GenerationLogModel.started_at.desc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(lg.id),
            "presentation_id": str(lg.presentation_id) if lg.presentation_id else None,
            "filename": lg.filename,
            "status": lg.status,
            "started_at": lg.started_at.isoformat() if lg.started_at else None,
            "finished_at": lg.finished_at.isoformat() if lg.finished_at else None,
            "total_duration_ms": lg.total_duration_ms,
            "error": lg.error,
            "steps_count": len(lg.steps) if lg.steps else 0,
        }
        for lg in logs
    ]


@ZACHET_ROUTER.get("/logs/{log_id}")
async def get_generation_log(
    log_id: uuid.UUID,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Get full generation log with all steps."""
    lg = await sql_session.get(GenerationLogModel, log_id)
    if not lg:
        raise HTTPException(status_code=404, detail="Generation log not found")
    return {
        "id": str(lg.id),
        "presentation_id": str(lg.presentation_id) if lg.presentation_id else None,
        "filename": lg.filename,
        "status": lg.status,
        "started_at": lg.started_at.isoformat() if lg.started_at else None,
        "finished_at": lg.finished_at.isoformat() if lg.finished_at else None,
        "total_duration_ms": lg.total_duration_ms,
        "error": lg.error,
        "steps": lg.steps or [],
    }


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
