from django.shortcuts import redirect, render

from cms.models import Language
from .utils import parse_language_payload


def language_create(request):
    initial = {"iso": "", "name": "", "short": "", "ai_note": ""}
    if request.method == "POST":
        payload, errors = parse_language_payload(request)
        if not errors:
            Language.objects.create(**payload)
            return redirect("language_list")
        return render(
            request,
            "cms/language_form.html",
            {"data": payload, "errors": errors, "mode": "create"},
        )

    return render(
        request,
        "cms/language_form.html",
        {"data": initial, "errors": [], "mode": "create"},
    )
