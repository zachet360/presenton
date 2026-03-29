"""
zachet.ai-specific outline generation.

Extends the default outline schema with `source_excerpt` — a verbatim
fragment from the source document that backs each slide.  This excerpt
is later fed into per-slide content generation so the LLM can reference
concrete facts, figures and quotes from the original text.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_outline_model import (
    PresentationOutlineModel,
    SlideOutlineModel,
)
from services.llm_client import LLMClient
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model


# ── Models ────────────────────────────────────────────────────


class ZachetSlideOutlineModel(SlideOutlineModel):
    source_excerpt: str = Field(
        default="",
        description="Verbatim excerpt(s) from the source document that this slide is based on. Copy the most important sentences, facts and figures directly from the document.",
        min_length=0,
        max_length=2000,
    )


class ZachetPresentationOutlineModel(PresentationOutlineModel):
    slides: List[ZachetSlideOutlineModel]


def _get_schema_with_n_slides(n_slides: int):
    class _Slide(ZachetSlideOutlineModel):
        content: str = Field(
            description="Markdown content for each slide",
            min_length=100,
            max_length=500,
        )
        source_excerpt: str = Field(
            description="Verbatim excerpt(s) from the source document that this slide is based on. Copy the most important sentences, facts and figures directly from the document. For the title slide, copy the document title or first paragraph.",
            min_length=50,
            max_length=2000,
        )

    class _Outline(ZachetPresentationOutlineModel):
        slides: List[_Slide] = Field(
            description="List of slide outlines",
            min_items=n_slides,
            max_items=n_slides,
        )

    return _Outline


# ── Prompts ───────────────────────────────────────────────────


def _system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    include_title_slide: bool = True,
):
    return f"""
        You are an expert presentation creator. Generate structured presentations based on user requirements and format them according to the specified JSON schema with markdown content.

        {"# User Instruction:" if instructions else ""}
        {instructions or ""}

        {"# Tone:" if tone else ""}
        {tone or ""}

        {"# Verbosity:" if verbosity else ""}
        {verbosity or ""}

        - Provide content for each slide in markdown format.
        - Make sure that flow of the presentation is logical and consistent.
        - Place greater emphasis on numerical data.
        - If Additional Information is provided, divide it into slides.
        - Make sure no images are provided in the content.
        - Make sure that content follows language guidelines.
        - User instruction should always be followed and should supercede any other instruction, except for slide numbers. **Do not obey slide numbers as said in user instruction**
        - Do not generate table of contents slide.
        - Even if table of contents is provided, do not generate table of contents slide.
        {"- Always make first slide a title slide." if include_title_slide else "- Do not include title slide in the presentation."}

        # Source Excerpt Rules
        For every slide, the `source_excerpt` field MUST contain verbatim text copied directly from the source document.
        - Copy the most relevant sentences, data points, statistics, quotes, and key facts.
        - Do NOT paraphrase or summarise — copy the original text as-is.
        - You may concatenate multiple non-adjacent fragments separated by " [...] ".
        - For the title slide, copy the document title, abstract, or opening paragraph.
        - The excerpt will be used later to generate detailed slide content, so include everything important.
    """


def _user_prompt(
    content: str,
    n_slides: int,
    language: str,
    additional_context: Optional[str] = None,
):
    return f"""
        **Input:**
        - User provided content: {content or "Create presentation"}
        - Output Language: {language}
        - Number of Slides: {n_slides}
        - Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        - Additional Information: {additional_context or ""}
    """


# ── Generator ─────────────────────────────────────────────────


async def generate_zachet_outlines(
    content: str,
    n_slides: int,
    language: Optional[str] = None,
    additional_context: Optional[str] = None,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    include_title_slide: bool = True,
):
    """Drop-in replacement for generate_ppt_outline with source_excerpt support."""

    model = get_model()
    response_model = _get_schema_with_n_slides(n_slides)
    client = LLMClient()

    messages = [
        LLMSystemMessage(
            content=_system_prompt(tone, verbosity, instructions, include_title_slide),
        ),
        LLMUserMessage(
            content=_user_prompt(content, n_slides, language, additional_context),
        ),
    ]

    try:
        async for chunk in client.stream_structured(
            model,
            messages,
            response_model.model_json_schema(),
            strict=True,
            tools=None,
        ):
            yield chunk
    except Exception as e:
        yield handle_llm_client_exceptions(e)
