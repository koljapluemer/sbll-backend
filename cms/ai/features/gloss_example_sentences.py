from django.conf import settings
from cms.ai.providers.openai_provider import OpenAIProvider
from cms.ai.logging import AIInteraction


def generate_example_sentences(gloss_content: str, source_language, translation_language=None, num_sentences: int = 3) -> dict:
    """
    Generate example sentences that demonstrate the usage of a gloss.

    Args:
        gloss_content: The gloss to generate example sentences for
        source_language: Language object with name, iso, and optional ai_note
        translation_language: Optional Language object for translation target (None = no translation)
        num_sentences: Number of example sentences to generate (default: 3)

    Returns:
        dict with 'sentences' list and 'interaction_id'
        sentences format:
        - With translation: [{"original": "...", "translation": "..."}, ...]
        - Without translation: [{"original": "...", "translation": None}, ...]
    """
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini"
    )

    # Build the prompt
    if translation_language:
        # Generate with translation
        prompt = f"""Generate exactly {num_sentences} example sentences in {source_language.name} ({source_language.iso}) that demonstrate the usage of the word or phrase: "{gloss_content}"

Each sentence should clearly show how "{gloss_content}" is used in context.

{f"Source language context: {source_language.ai_note}" if source_language.ai_note else ""}

Then translate each sentence to {translation_language.name} ({translation_language.iso}).

{f"Target language context: {translation_language.ai_note}" if translation_language.ai_note else ""}

Return ONLY a JSON array of objects with "original" and "translation" keys. Example format:
[
  {{"original": "sentence in {source_language.iso}", "translation": "sentence in {translation_language.iso}"}},
  {{"original": "sentence in {source_language.iso}", "translation": "sentence in {translation_language.iso}"}}
]"""
    else:
        # Generate without translation
        prompt = f"""Generate exactly {num_sentences} example sentences in {source_language.name} ({source_language.iso}) that demonstrate the usage of the word or phrase: "{gloss_content}"

Each sentence should clearly show how "{gloss_content}" is used in context.

{f"Language-specific context: {source_language.ai_note}" if source_language.ai_note else ""}

Return ONLY a JSON array of strings. Example format:
["example sentence 1", "example sentence 2", "example sentence 3"]"""

    result = provider.generate(prompt)

    # Parse the JSON response
    import json
    try:
        parsed_output = json.loads(result["output"])

        # Normalize to consistent format
        if translation_language:
            # Expected format: [{"original": "...", "translation": "..."}, ...]
            sentences = parsed_output
        else:
            # Convert string array to object array format
            # Format: ["sentence 1", "sentence 2"] -> [{"original": "sentence 1", "translation": None}, ...]
            sentences = [{"original": sentence, "translation": None} for sentence in parsed_output]
    except json.JSONDecodeError:
        # Fallback if response isn't valid JSON
        sentences = [{"original": result["output"], "translation": None}]

    # Log the interaction
    interaction = AIInteraction.objects.create(
        feature="gloss_example_sentences",
        input_data={
            "gloss_content": gloss_content,
            "source_language_iso": source_language.iso,
            "source_language_name": source_language.name,
            "translation_language_iso": translation_language.iso if translation_language else None,
            "translation_language_name": translation_language.name if translation_language else None,
            "num_sentences": num_sentences,
        },
        logging_data={
            **result["metadata"],
            "num_sentences": num_sentences,
            "has_translation": translation_language is not None,
            "has_source_ai_note": bool(source_language.ai_note),
            "has_target_ai_note": bool(translation_language.ai_note) if translation_language else False,
        },
        output_data={
            "sentences": sentences,
        }
    )

    return {
        "sentences": sentences,
        "interaction_id": interaction.id,
    }
