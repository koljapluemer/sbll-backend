from django.conf import settings
from cms.ai.providers.openai_provider import OpenAIProvider
from cms.ai.logging import AIInteraction


def generate_translations(glosses: list, target_language) -> dict:
    """
    Generate translations for multiple glosses.

    Args:
        glosses: List of Gloss objects to translate
        target_language: Target Language object

    Returns:
        dict with 'translations' list of dicts and 'interaction_id'
    """
    provider = OpenAIProvider(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini"
    )

    # Build list of texts to translate
    texts = [{"id": g.id, "content": g.content, "language": g.language.name} for g in glosses]
    source_language = glosses[0].language  # Assume all same source language

    # Build prompt
    prompt = f"""Translate the following {source_language.name} ({source_language.iso}) texts to {target_language.name} ({target_language.iso}).

{f"Target language context: {target_language.ai_note}" if target_language.ai_note else ""}
{f"Source language context: {source_language.ai_note}" if source_language.ai_note else ""}

Texts to translate:
{chr(10).join(f'{i+1}. "{t["content"]}"' for i, t in enumerate(texts))}

Return ONLY a JSON array of translations in the same order, nothing else. Example format:
["translation 1", "translation 2", "translation 3"]"""

    result = provider.generate(prompt)

    # Parse JSON response
    import json
    try:
        translations_raw = json.loads(result["output"])
    except json.JSONDecodeError:
        # Fallback: split by newlines
        translations_raw = result["output"].strip().split('\n')

    # Pair translations with source gloss IDs
    translations = []
    for i, gloss in enumerate(glosses):
        translation_text = translations_raw[i] if i < len(translations_raw) else ""
        translations.append({
            "source_id": gloss.id,
            "source_content": gloss.content,
            "translation": translation_text.strip('"').strip(),
        })

    # Log interaction
    interaction = AIInteraction.objects.create(
        feature="gloss_translation",
        input_data={
            "num_glosses": len(glosses),
            "source_language_iso": source_language.iso,
            "target_language_iso": target_language.iso,
            "glosses": [{"id": g.id, "content": g.content} for g in glosses],
        },
        logging_data={
            **result["metadata"],
            "num_glosses": len(glosses),
            "source_language_iso": source_language.iso,
            "target_language_iso": target_language.iso,
            "has_source_ai_note": bool(source_language.ai_note),
            "has_target_ai_note": bool(target_language.ai_note),
        },
        output_data={
            "translations": translations,
        }
    )

    return {
        "translations": translations,
        "interaction_id": interaction.id,
    }
