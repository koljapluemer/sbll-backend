from django.shortcuts import render

from cms.models import Language, Situation


def situation_export_form(request):
    """
    Display form for selecting languages and situation for gloss export.
    """
    languages = Language.objects.all().order_by("name")
    situations = Situation.objects.all().order_by("id")

    # Pre-select situation if provided in query parameter
    selected_situation = request.GET.get("situation", "")

    return render(
        request,
        "cms/situation_export_form.html",
        {
            "languages": languages,
            "situations": situations,
            "selected_situation": selected_situation,
        },
    )
