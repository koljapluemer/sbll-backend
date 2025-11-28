from django.shortcuts import render

from cms.models import Gloss


def gloss_list(request):
    glosses = (
        Gloss.objects.select_related("language")
        .prefetch_related("translations", "near_synonyms")
        .order_by("language__iso", "content")
    )
    return render(request, "cms/gloss_list.html", {"glosses": glosses})
