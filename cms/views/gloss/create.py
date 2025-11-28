from django.shortcuts import redirect, render
from django.urls import reverse

from cms.models import Gloss, Language
from cms.views.shared.utils import serialize_languages
from .utils import parse_gloss_form_payload, serialize_relations


def gloss_create(request):
    languages = Language.objects.order_by("name")
    languages_serialized = serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create_or_get")
    empty = {
        "content": "",
        "language": None,
        "transcriptions_raw": "",
        "relations": {key: [] for key in [
            "contains",
            "near_synonyms",
            "near_homophones",
            "translations",
            "clarifies_usage",
            "to_be_differentiated_from",
            "collocations",
        ]},
    }
    if request.method == "POST":
        payload, errors = parse_gloss_form_payload(request)
        if not errors:
            gloss = Gloss.objects.create(
                content=payload["content"],
                language=payload["language"],
                transcriptions=payload["transcriptions"],
            )
            for relation_name, values in payload["relations"].items():
                getattr(gloss, relation_name).set(values)
            return redirect("gloss_list")
        return render(
            request,
            "cms/gloss_form.html",
            {
                "data": payload,
                "errors": errors,
                "languages": languages,
                "languages_serialized": languages_serialized,
                "relations_serialized": serialize_relations(payload["relations"]),
                "gloss_search_url": gloss_search_url,
                "gloss_create_url": gloss_create_url,
                "mode": "create",
            },
        )

    return render(
        request,
        "cms/gloss_form.html",
        {
            "data": empty,
            "errors": [],
            "languages": languages,
            "languages_serialized": languages_serialized,
            "relations_serialized": serialize_relations(empty["relations"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "mode": "create",
        },
    )
