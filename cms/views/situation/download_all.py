import io
import json
import zipfile
from collections import defaultdict

from django.http import HttpResponse

from cms.models import Language, Situation
from cms.views.gloss.utils import collect_glosses_recursively, serialize_gloss_to_jsonl


def situation_download_all(request):
    """
    Download all situations across all valid language pairs as a ZIP file.

    Generates a ZIP containing:
    - Individual situation JSONL files for each valid language pair
    - Index files: native_languages.jsonl, target_languages.jsonl
    - Per-pair index files: situations_{target_iso}_{native_iso}.jsonl

    Validation:
    - Situation must have descriptions in both languages
    - Collected glosses must contain at least one gloss in each language

    POST only endpoint.

    Returns:
        HttpResponse with ZIP file or 404 if no valid pairs found
    """
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    # Initialize tracking structures
    valid_situations_by_pair = defaultdict(list)
    native_languages_set = set()
    target_languages_set = set()

    # Cache all languages to avoid repeated queries
    all_languages = list(Language.objects.all())

    # Loop through all situations
    for situation in Situation.objects.all():
        # Get available description languages for this situation
        description_languages = set(
            situation.descriptions.select_related("language").values_list(
                "language__iso", flat=True
            )
        )

        # Loop through all language pairs
        for target_lang in all_languages:
            for native_lang in all_languages:
                # Skip same language pairs
                if target_lang.iso == native_lang.iso:
                    continue

                # Validation Check 1: Both descriptions must exist
                if (
                    target_lang.iso not in description_languages
                    or native_lang.iso not in description_languages
                ):
                    continue

                # Collect glosses recursively
                glosses = collect_glosses_recursively(
                    situation, native_lang.iso, target_lang.iso
                )

                # Filter out paraphrased glosses in target language
                # (native language glosses are kept regardless)
                filtered_glosses = [
                    g for g in glosses
                    if not (g.language.iso == target_lang.iso and g.is_paraphrased())
                ]

                # Validation Check 2: Must have at least one gloss in each language
                language_isos = {g.language.iso for g in filtered_glosses}
                if (
                    native_lang.iso not in language_isos
                    or target_lang.iso not in language_isos
                ):
                    continue

                # Generate JSONL content
                jsonl_lines = []
                for gloss in filtered_glosses:
                    # Prefetch relationships to avoid N+1 queries during serialization
                    gloss.contains.all()
                    gloss.translations.all()
                    gloss.near_synonyms.all()
                    gloss.near_homophones.all()
                    gloss.clarifies_usage.all()
                    gloss.to_be_differentiated_from.all()
                    gloss.collocations.all()
                    gloss.usage_of_clarified.all()
                    serialized = serialize_gloss_to_jsonl(gloss, target_language_iso=target_lang.iso)
                    jsonl_lines.append(json.dumps(serialized, ensure_ascii=False))

                jsonl_content = "\n".join(jsonl_lines)

                # Get descriptions
                target_description = (
                    situation.descriptions.filter(language=target_lang).first().content
                )
                native_description = (
                    situation.descriptions.filter(language=native_lang).first().content
                )

                # Store valid situation data
                pair_key = f"{target_lang.iso}_{native_lang.iso}"
                valid_situations_by_pair[pair_key].append(
                    {
                        "situation_id": situation.id,
                        "jsonl_content": jsonl_content,
                        "target_description": target_description,
                        "native_description": native_description,
                        "image_link": situation.image_link or "",
                    }
                )

                # Track languages used
                native_languages_set.add(native_lang.iso)
                target_languages_set.add(target_lang.iso)

    # Check if we found any valid situations
    if not valid_situations_by_pair:
        return HttpResponse("No valid language pairs found for export", status=404)

    # Generate ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add situation JSONL files
        for pair_key, situations in valid_situations_by_pair.items():
            for sit_data in situations:
                filename = f"{sit_data['situation_id']}_{pair_key}.jsonl"
                zip_file.writestr(filename, sit_data["jsonl_content"])

        # Add native_languages.jsonl
        native_langs = Language.objects.filter(iso__in=native_languages_set).order_by(
            "name"
        )
        native_data = [
            {"iso": lang.iso, "name": lang.name, "short": lang.short or ""}
            for lang in native_langs
        ]
        zip_file.writestr(
            "native_languages.jsonl",
            "\n".join(json.dumps(d, ensure_ascii=False) for d in native_data),
        )

        # Add target_languages.jsonl
        target_langs = Language.objects.filter(iso__in=target_languages_set).order_by(
            "name"
        )
        target_data = [
            {"iso": lang.iso, "name": lang.name, "short": lang.short or ""}
            for lang in target_langs
        ]
        zip_file.writestr(
            "target_languages.jsonl",
            "\n".join(json.dumps(d, ensure_ascii=False) for d in target_data),
        )

        # Add situations_{target}_{native}.jsonl index files
        for pair_key, situations in valid_situations_by_pair.items():
            index_data = [
                {
                    "id": sit["situation_id"],
                    "target_description": sit["target_description"],
                    "native_description": sit["native_description"],
                    "image_link": sit["image_link"],
                }
                for sit in situations
            ]

            filename = f"situations_{pair_key}.jsonl"
            zip_file.writestr(
                filename, "\n".join(json.dumps(d, ensure_ascii=False) for d in index_data)
            )

    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="sbll_all_situations.zip"'

    return response
