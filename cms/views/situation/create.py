from django.shortcuts import redirect, render
from django.urls import reverse

from cms.models import Gloss, Language, Situation
from cms.views.shared.utils import serialize_languages
from .utils import parse_situation_payload, serialize_glosses


def situation_create(request):
    glosses = Gloss.objects.order_by("content")
    languages = Language.objects.order_by("name")
    languages_serialized = serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")
    empty = {"id": "", "glosses": []}
    if request.method == "POST":
        payload, errors = parse_situation_payload(request)
        if not errors:
            situation = Situation.objects.create(id=payload["id"])
            situation.glosses.set(payload["glosses"])
            return redirect("situation_list")
        return render(
            request,
            "cms/situation_form.html",
            {
                "data": payload,
                "errors": errors,
                "mode": "create",
                "glosses": glosses,
                "languages": languages,
                "languages_serialized": languages_serialized,
                "glosses_serialized": serialize_glosses(payload["glosses"]),
                "gloss_search_url": gloss_search_url,
                "gloss_create_url": gloss_create_url,
            },
        )

    return render(
        request,
        "cms/situation_form.html",
        {
            "data": empty,
            "errors": [],
            "mode": "create",
            "glosses": glosses,
            "languages": languages,
            "languages_serialized": languages_serialized,
            "glosses_serialized": serialize_glosses(empty["glosses"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
        },
    )
