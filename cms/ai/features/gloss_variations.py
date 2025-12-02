from django.conf import settings
from cms.ai.providers.openai_provider import OpenAIProvider
from cms.ai.logging import AIInteraction


def generate_variations(gloss_content: str, language, num_variations: int = 3) -> dict:
    """
    Generate variations of a gloss sentence.

    Args:
        gloss_content: The sentence to generate variations for
        language: Language object with name, iso, and optional ai_note
        num_variations: Number of variations to generate (3 or 5)

    Returns:
        dict with 'variations' list and 'interaction_id'
    """
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini"
    )

    prompt = f"""Generate exactly {num_variations} variations of the following sentence in {language.name} ({language.iso}):

"{gloss_content}"

{f"Language-specific context: {language.ai_note}" if language.ai_note else ""}

Create variations that change:
- Politeness level (more formal or more casual)
- Slang usage
- Word order
- Word choices (synonyms)

Return ONLY a JSON array of strings, nothing else. Example format:
["variation 1", "variation 2", "variation 3"]"""

    result = provider.generate(prompt)

    # Parse the JSON response
    import json
    try:
        variations = json.loads(result["output"])
    except json.JSONDecodeError:
        # Fallback if response isn't valid JSON
        variations = [result["output"]]

    # Log the interaction
    interaction = AIInteraction.objects.create(
        feature="gloss_variations",
        input_data={
            "gloss_content": gloss_content,
            "language_iso": language.iso,
            "language_name": language.name,
            "num_variations": num_variations,
        },
        logging_data={
            **result["metadata"],
            "num_variations": num_variations,
            "language_iso": language.iso,
            "has_ai_note": bool(language.ai_note),
        },
        output_data={
            "variations": variations,
        }
    )

    return {
        "variations": variations,
        "interaction_id": interaction.id,
    }
