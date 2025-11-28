from django.shortcuts import get_object_or_404, redirect, render

from cms.models import Language
from .utils import parse_language_payload


def language_update(request, pk):
    language = get_object_or_404(Language, pk=pk)
    if request.method == "POST":
        payload, errors = parse_language_payload(request, instance=language)
        if not errors:
            language.name = payload["name"]
            language.short = payload["short"]
            language.ai_note = payload["ai_note"]
            language.save()
            return redirect("language_list")
        return render(
            request,
            "cms/language_form.html",
            {"data": payload, "errors": errors, "mode": "edit", "language": language},
        )

    data = {"iso": language.iso, "name": language.name, "short": language.short or "", "ai_note": language.ai_note or ""}
    return render(
        request,
        "cms/language_form.html",
        {"data": data, "errors": [], "mode": "edit", "language": language},
    )
