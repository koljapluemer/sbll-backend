from django.shortcuts import render
from django.core.paginator import Paginator

from cms.models import Gloss, Language


def tools_untranslated_glosses(request):
    """Find glosses that exist in native language but not in target language."""
    native_iso = request.GET.get("native", "").strip()
    target_iso = request.GET.get("lang", "").strip()

    # Get all languages for the form dropdowns
    languages = Language.objects.order_by("name")

    # Initialize context
    context = {
        "languages": languages,
        "native_iso": native_iso,
        "target_iso": target_iso,
        "glosses": None,
        "page_obj": None,
    }

    # If both parameters are provided, perform the search
    if native_iso and target_iso:
        # Query: glosses in native language without translation to target language
        glosses = (
            Gloss.objects
            .filter(language__iso=native_iso)
            .exclude(translations__language__iso=target_iso)
            .select_related("language")
            .prefetch_related("translations")
            .order_by("content")
        )

        # Paginate results (50 per page)
        paginator = Paginator(glosses, 50)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["glosses"] = page_obj.object_list

    return render(request, "cms/tools_untranslated_glosses.html", context)
