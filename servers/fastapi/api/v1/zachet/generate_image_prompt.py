"""
zachet.ai-specific image prompt generation (LLM #4).

After slide content is generated, this module takes the finished slide
text + source_excerpt + document summary and produces an optimised
image search query for Yandex Image Search or YandexART.
"""

from typing import Optional

from models.llm_message import LLMSystemMessage, LLMUserMessage
from services.llm_client import LLMClient
from utils.image_provider import is_yandex_selected
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model


_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "image_prompt": {
            "type": "string",
            "description": "Optimised image search query",
            "minLength": 5,
            "maxLength": 150,
        },
    },
    "required": ["image_prompt"],
}


def _system_prompt() -> str:
    if is_yandex_selected():
        lang_instruction = "Write the search query in RUSSIAN."
    else:
        lang_instruction = "Write the search query in ENGLISH."

    return f"""You are an image search specialist. Your task is to write the best possible image search query for a presentation slide.

{lang_instruction}

# Rules
- You receive: the slide's text content, a source document excerpt, a document summary, and the desired image type.
- Return a single search query optimised for finding a highly relevant image.
- The query should be 3-8 words, concrete and specific.
- Avoid generic terms like "people working", "abstract background", "business meeting", "students studying".
- Match the query to the image type:
  - "photo": search for a real photograph — name specific objects, places, phenomena
  - "diagram": search for a schema, chart, infographic — name the exact process or data structure
  - "illustration": describe a concrete visual concept for AI generation — include style hints (flat design, isometric, etc.)

# Examples (Russian)
- Slide about cell membrane structure, type=photo → "клеточная мембрана электронная микрография"
- Slide about GDP growth 2020-2024, type=diagram → "график рост ВВП России 2020 2024"
- Slide about AI in education, type=illustration → "нейросеть обучение студент изометрическая иллюстрация"

# Examples (English)
- Slide about photosynthesis, type=diagram → "photosynthesis process diagram labeled chloroplast"
- Slide about Renaissance art, type=photo → "Sistine Chapel ceiling Michelangelo fresco"
- Slide about quantum computing, type=illustration → "quantum computer qubit isometric flat design"
"""


def _user_prompt(
    slide_content_text: str,
    image_type: str,
    source_excerpt: str,
    document_summary: str,
) -> str:
    return f"""# Image type
{image_type}

# Slide content
{slide_content_text}

# Source document excerpt for this slide
{source_excerpt}

# Document summary
{document_summary}
"""


def _extract_text_from_slide_content(content: dict) -> str:
    """Extract human-readable text from a slide content dict for context."""
    parts = []
    for key, value in content.items():
        if key.startswith("__"):
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str) and not v.startswith("__"):
                            parts.append(v)
    return "\n".join(parts[:20])  # cap to avoid huge prompts


async def generate_image_prompt(
    slide_content: dict,
    image_type: str,
    source_excerpt: str = "",
    document_summary: str = "",
) -> str:
    """Generate an optimised image search prompt for a single slide."""

    client = LLMClient()
    model = get_model()

    slide_text = _extract_text_from_slide_content(slide_content)

    messages = [
        LLMSystemMessage(content=_system_prompt()),
        LLMUserMessage(
            content=_user_prompt(slide_text, image_type, source_excerpt, document_summary),
        ),
    ]

    try:
        response = await client.generate_structured(
            model=model,
            messages=messages,
            response_format=_RESPONSE_SCHEMA,
            strict=False,
            max_tokens=200,
        )
        prompt = response.get("image_prompt", "")
        print(f"[ImagePromptGen] type={image_type} → '{prompt}'")
        return prompt
    except Exception as e:
        print(f"[ImagePromptGen] Error: {e}, falling back to original")
        raise handle_llm_client_exceptions(e)
