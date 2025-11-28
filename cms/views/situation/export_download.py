import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from cms.models import Situation
from cms.views.gloss.utils import collect_glosses_recursively, serialize_gloss_to_jsonl


def situation_export_download(request):
    """
    Handle the download of glosses in JSONL format for a given situation and language pair.

    POST parameters:
        - native_language: ISO code of the native language
        - target_language: ISO code of the target language
        - situation: ID of the situation

    Returns:
        HttpResponse with JSONL content for download
    """
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    # Get form data
    native_language_iso = request.POST.get("native_language", "").strip()
    target_language_iso = request.POST.get("target_language", "").strip()
    situation_id = request.POST.get("situation", "").strip()

    # Validate inputs
    if not all([native_language_iso, target_language_iso, situation_id]):
        return HttpResponse("Missing required parameters", status=400)

    # Get the situation
    situation = get_object_or_404(Situation, pk=situation_id)

    # Collect glosses recursively based on the language filters
    glosses = collect_glosses_recursively(
        situation, native_language_iso, target_language_iso
    )

    # Prefetch related data for efficient serialization
    # This avoids N+1 queries when serializing relationships and notes
    glosses_with_relations = []
    for gloss in glosses:
        # Force evaluation of relationships to avoid additional queries during serialization
        gloss.contains.all()
        gloss.translations.all()
        gloss.note_set.all()
        glosses_with_relations.append(gloss)

    # Serialize to JSONL format (one JSON object per line)
    jsonl_lines = []
    for gloss in glosses_with_relations:
        serialized = serialize_gloss_to_jsonl(gloss)
        jsonl_lines.append(json.dumps(serialized, ensure_ascii=False))

    jsonl_content = "\n".join(jsonl_lines)

    # Create filename
    filename = f"glosses_{situation_id}_{native_language_iso}_{target_language_iso}.jsonl"

    # Create response with proper headers for download
    response = HttpResponse(jsonl_content, content_type="application/jsonl")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
