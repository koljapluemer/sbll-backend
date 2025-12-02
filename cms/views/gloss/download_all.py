import io
import json
import zipfile
import re

from django.http import HttpResponse
from cms.models import Gloss
from cms.views.gloss.utils import serialize_gloss_to_json


def gloss_download_all(request):
    """
    Download all glosses as individual JSON files in a ZIP archive.

    Each gloss becomes a separate JSON file named {iso_code}:{content}.json
    with all its data and relationships.

    GET endpoint.

    Returns:
        HttpResponse with ZIP file
    """

    # Get all glosses with prefetched relationships
    glosses = Gloss.objects.select_related('language').prefetch_related(
        'contains',
        'translations',
        'near_synonyms',
        'near_homophones',
        'clarifies_usage',
        'to_be_differentiated_from',
        'collocations',
        'usage_of_clarified',
    ).all()

    # Generate ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for gloss in glosses:
            # Serialize gloss to dict
            gloss_data = serialize_gloss_to_json(gloss)

            # Remove only illegal filesystem characters: < > : " / \ | ? *
            safe_content = re.sub(r'[<>:"/\\|?*]', '', gloss.content)

            # Get first two letters for folder structure (or first letter if only one char)
            first_two = safe_content[:2] if len(safe_content) >= 2 else safe_content[:1]

            # Create path: {language}/{first_two}/{iso_code}:{content}.json
            filepath = f"{gloss.language.iso}/{first_two}/{gloss.language.iso}:{safe_content}.json"

            # Write JSON to ZIP
            json_content = json.dumps(gloss_data, ensure_ascii=False, indent=2)
            zip_file.writestr(filepath, json_content)

    # Prepare response
    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="sbll_all_glosses.zip"'

    return response
