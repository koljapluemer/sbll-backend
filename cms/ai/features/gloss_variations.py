from django.conf import settings
from cms.ai.providers.openai_provider import OpenAIProvider
from cms.ai.logging import AIInteraction


def generate_variations(gloss_content: str, num_variations: int = 3) -> dict:
    """
    Generate variations of a gloss sentence.

    Args:
        gloss_content: The sentence to generate variations for
        num_variations: Number of variations to generate (3 or 5)

    Returns:
        dict with 'variations' list and 'interaction_id'
    """
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini"
    )

    prompt = f"""Generate exactly {num_variations} variations of the following sentence:

"{gloss_content}"

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
            "num_variations": num_variations,
        },
        logging_data={
            **result["metadata"],
            "num_variations": num_variations,
        },
        output_data={
            "variations": variations,
        }
    )

    return {
        "variations": variations,
        "interaction_id": interaction.id,
    }
