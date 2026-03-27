from datetime import datetime
from typing import Optional
from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.presentation_layout import SlideLayoutModel
from models.presentation_outline_model import SlideOutlineModel
from services.llm_client import LLMClient
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model
from utils.image_provider import is_yandex_selected
from utils.schema_utils import add_field_in_schema, remove_fields_from_schema


def _get_image_prompt_instructions() -> str:
    if is_yandex_selected():
        return """Write in RUSSIAN. Use 2-4 short, concrete keywords that describe the core visual concept of the slide. Optimize for image search — use nouns and specific terms, no generic words.

          For "photo" type:
            "Клеточная мембрана" -> "клеточная мембрана электронный микроскоп"
            "Вторая мировая война" -> "советские солдаты 1943 война"
            "Озеро Байкал" -> "Байкал вид сверху"

          For "diagram" type:
            "Спрос и предложение" -> "график спрос предложение экономика"
            "Фотосинтез" -> "схема фотосинтез хлоропласт"
            "Цикл Кребса" -> "цикл Кребса схема биохимия"

          For "illustration" type:
            "Искусственный интеллект" -> "нейронная сеть иллюстрация концепция"
            "Энергетика будущего" -> "возобновляемая энергетика солнечные панели ветряки"""

    return """ALWAYS write in English regardless of presentation language. Be hyper-specific to the slide's CORE educational concept:

          For "photo" type:
            "Cell membrane" -> "electron microscope photograph cell membrane"
            "World War 2" -> "World War 2 Soviet soldiers 1943 historical photo"
            "Lake Baikal" -> "Lake Baikal aerial view crystal clear water"

          For "diagram" type:
            "Supply and demand" -> "supply demand curve economics diagram labeled axes"
            "Photosynthesis" -> "photosynthesis process diagram chloroplast labeled"
            "Krebs cycle" -> "Krebs cycle biochemistry diagram with molecules"

          For "illustration" type:
            "Artificial Intelligence" -> "neural network concept illustration connected nodes blue tones flat design white background"
            "Future of energy" -> "futuristic renewable energy landscape solar panels wind turbines isometric illustration" """


def get_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    presentation_context: Optional[str] = None,
):
    context_block = ""
    if presentation_context:
        context_block = f"""
        # Presentation Context
        {presentation_context}
        Use this context to ensure all slide images and content are relevant to the overall presentation topic.
        """

    return f"""
        Generate structured slide based on provided outline, follow mentioned steps and notes and provide structured output.

        {"# User Instructions:" if instructions else ""}
        {instructions or ""}

        {"# Tone:" if tone else ""}
        {tone or ""}

        {"# Verbosity:" if verbosity else ""}
        {verbosity or ""}

        {context_block}

        # Steps
        1. Analyze the outline.
        2. Generate structured slide based on the outline.
        3. Generate speaker note that is simple, clear, concise and to the point.

        # Notes
        - Slide body should not use words like "This slide", "This presentation".
        - Rephrase the slide body to make it flow naturally.
        - Only use markdown to highlight important points.
        - Make sure to follow language guidelines.
        - Speaker note should be normal text, not markdown.
        - Strictly follow the max and min character limit for every property in the slide.
        - Never ever go over the max character limit. Limit your narration to make sure you never go over the max character limit.
        - Number of items should not be more than max number of items specified in slide schema. If you have to put multiple points then merge them to obey max numebr of items.
        - Generate content as per the given tone.
        - Be very careful with number of words to generate for given field. As generating more than max characters will overflow in the design. So, analyze early and never generate more characters than allowed.
        - Do not add emoji in the content.
        - Metrics should be in abbreviated form with least possible characters. Do not add long sequence of words for metrics.
        - For verbosity:
            - If verbosity is 'concise', then generate description as 1/3 or lower of the max character limit. Don't worry if you miss content or context.
            - If verbosity is 'standard', then generate description as 2/3 of the max character limit.
            - If verbosity is 'text-heavy', then generate description as 3/4 or higher of the max character limit. Make sure it does not exceed the max character limit.

        User instructions, tone and verbosity should always be followed and should supercede any other instruction, except for max and min character limit, slide schema and number of items.

        - Provide output in json format and **don't include <parameters> tags**.

        # Image and Icon Output Format
        For each slide's image, provide TWO fields:

        __image_type__: Choose ONE of:
          - "photo" - for real photographs (historical events, places, people, nature, biological specimens, architectural landmarks, portraits of scientists/writers/historical figures).
          - "diagram" - for diagrams, schemes, charts, infographics, maps, flowcharts, timelines, process visualizations.
          - "illustration" - for AI-generated conceptual illustrations when no good real photo or diagram exists (abstract concepts, decorative slides, futuristic/hypothetical scenarios).

        __image_prompt__: {_get_image_prompt_instructions()}

          MAPPING RULES:
          - Slides with data/statistics -> "diagram"
          - Slides about historical events/real places/real people -> "photo"
          - Slides with processes/steps/structures -> "diagram"
          - Title/intro slides -> "illustration" or "photo" of the main topic
          - Conclusion slides -> "illustration" summarizing the concept
          - Slides about abstract concepts with no real-world visual -> "illustration"

          NEVER generate generic descriptions like "students studying", "people at computers", "abstract technology background", "business handshake", or "group of people working together".

        image: {{
            __image_type__: string,
            __image_prompt__: string,
        }}
        icon: {{
            __icon_query__: string,
        }}

    """


def get_user_prompt(outline: str, language: str):
    image_language = "Russian" if is_yandex_selected() else "English"
    return f"""
        ## Current Date and Time
        {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        ## Icon Query And Image Prompt Language
        {image_language}

        ## Slide Content Language
        {language}

        ## Slide Outline
        {outline}
    """


def get_messages(
    outline: str,
    language: str,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    presentation_context: Optional[str] = None,
):

    return [
        LLMSystemMessage(
            content=get_system_prompt(tone, verbosity, instructions, presentation_context),
        ),
        LLMUserMessage(
            content=get_user_prompt(outline, language),
        ),
    ]


async def get_slide_content_from_type_and_outline(
    slide_layout: SlideLayoutModel,
    outline: SlideOutlineModel,
    language: str,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    presentation_context: Optional[str] = None,
):
    client = LLMClient()
    model = get_model()

    response_schema = remove_fields_from_schema(
        slide_layout.json_schema, ["__image_url__", "__icon_url__"]
    )
    response_schema = add_field_in_schema(
        response_schema,
        {
            "__speaker_note__": {
                "type": "string",
                "minLength": 100,
                "maxLength": 250,
                "description": "Speaker note for the slide",
            }
        },
        True,
    )

    messages = get_messages(
        outline.content,
        language,
        tone,
        verbosity,
        instructions,
        presentation_context,
    )
    print(
        f"get_slide_content_from_type_and_outline: model={model} outline_len={len(outline.content or '')} language={language}"
    )
    try:
        response = await client.generate_structured(
            model=model,
            messages=messages,
            response_format=response_schema,
            strict=False,
        )
        print(
            f"get_slide_content_from_type_and_outline: response is None={response is None} keys={list(response.keys())[:6] if isinstance(response, dict) else None}"
        )
        return response

    except Exception as e:
        print(f"get_slide_content_from_type_and_outline: exception={e}")
        raise handle_llm_client_exceptions(e)
