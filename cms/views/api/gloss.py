from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from cms.models import Gloss, Language


def _serialize_gloss(gloss):
    """Serialize a gloss object for API responses."""
    return {
        "id": gloss.pk,
        "label": f"{gloss.language.iso}: {gloss.content}",
        "content": gloss.content,
        "language_iso": gloss.language.iso,
    }


@require_GET
def api_gloss_search(request):
    """Search for glosses by content."""
    query = request.GET.get("q", "").strip()
    qs = Gloss.objects.select_related("language")
    if query:
        qs = qs.filter(content__icontains=query)
    results = [_serialize_gloss(gloss) for gloss in qs.order_by("content")[:10]]
    return JsonResponse({"results": results})


@require_POST
def api_gloss_create(request):
    """Create a new gloss via API."""
    content = request.POST.get("content", "").strip()
    language_iso = request.POST.get("language", "").strip()
    if not content:
        return JsonResponse({"error": "Content is required."}, status=400)
    if not language_iso:
        return JsonResponse({"error": "Language is required."}, status=400)
    language = Language.objects.filter(pk=language_iso).first()
    if not language:
        return JsonResponse({"error": "Language not found."}, status=404)

    gloss = Gloss.objects.create(content=content, language=language, transcriptions=[])
    return JsonResponse({"gloss": _serialize_gloss(gloss)})
