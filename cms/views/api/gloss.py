from django.db import IntegrityError
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
    """Search for glosses by content, optionally filtered by language."""
    query = request.GET.get("q", "").strip()
    language_iso = request.GET.get("language", "").strip()

    qs = Gloss.objects.select_related("language")

    if query:
        qs = qs.filter(content__icontains=query)

    if language_iso:
        qs = qs.filter(language__iso=language_iso)

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


@require_POST
def api_gloss_create_or_get(request):
    """
    Get existing gloss or create new one if lang+content doesn't exist.
    Uses atomic get_or_create to prevent race conditions.
    """
    content = request.POST.get("content", "").strip()
    language_iso = request.POST.get("language", "").strip()

    # Validation
    if not content:
        return JsonResponse({"error": "Content is required."}, status=400)
    if not language_iso:
        return JsonResponse({"error": "Language is required."}, status=400)

    try:
        language = Language.objects.get(pk=language_iso)
    except Language.DoesNotExist:
        return JsonResponse({"error": "Language not found."}, status=404)

    try:
        # Atomic operation: get existing or create new
        gloss, created = Gloss.objects.get_or_create(
            content=content,
            language=language,
            defaults={'transcriptions': []}
        )

        return JsonResponse({
            "gloss": _serialize_gloss(gloss),
            "created": created,
            "status": "created" if created else "existing"
        })

    except IntegrityError:
        # Race condition: try to get the gloss that was just created
        try:
            gloss = Gloss.objects.get(content=content, language=language)
            return JsonResponse({
                "gloss": _serialize_gloss(gloss),
                "created": False,
                "status": "existing"
            })
        except Gloss.DoesNotExist:
            return JsonResponse({
                "error": "Database error - please try again"
            }, status=409)

    except Exception as e:
        return JsonResponse({
            "error": "An unexpected error occurred"
        }, status=500)
