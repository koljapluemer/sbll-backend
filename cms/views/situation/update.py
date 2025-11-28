from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cms.models import Gloss, Language, Situation
from cms.views.shared.utils import serialize_languages
from .utils import parse_situation_payload, serialize_glosses


def situation_update(request, pk):
    situation = get_object_or_404(Situation, pk=pk)
    glosses = Gloss.objects.order_by("content")
    languages = Language.objects.order_by("name")
    languages_serialized = serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")

    if request.method == "POST":
        payload, errors = parse_situation_payload(request, instance=situation)
        if not errors:
            situation.glosses.set(payload["glosses"])
            return redirect("situation_list")
        return render(
            request,
            "cms/situation_form.html",
            {
                "data": payload,
                "errors": errors,
                "mode": "edit",
                "glosses": glosses,
                "languages": languages,
                "languages_serialized": languages_serialized,
                "glosses_serialized": serialize_glosses(payload["glosses"]),
                "gloss_search_url": gloss_search_url,
                "gloss_create_url": gloss_create_url,
                "situation": situation,
            },
        )

    data = {"id": situation.id, "glosses": list(situation.glosses.all())}
    return render(
        request,
        "cms/situation_form.html",
        {
            "data": data,
            "errors": [],
            "mode": "edit",
            "glosses": glosses,
            "languages": languages,
            "languages_serialized": languages_serialized,
            "glosses_serialized": serialize_glosses(data["glosses"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "situation": situation,
        },
    )
