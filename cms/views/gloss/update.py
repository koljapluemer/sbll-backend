from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cms.models import Gloss, Language
from cms.views.shared.utils import serialize_languages
from .utils import parse_gloss_form_payload, serialize_relations


def gloss_update(request, pk):
    gloss = get_object_or_404(Gloss, pk=pk)
    languages = Language.objects.order_by("name")
    languages_serialized = serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")
    if request.method == "POST":
        payload, errors = parse_gloss_form_payload(request, instance=gloss)
        if not errors:
            gloss.content = payload["content"]
            gloss.language = payload["language"]
            gloss.transcriptions = payload["transcriptions"]
            gloss.save()
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
                "mode": "edit",
                "gloss": gloss,
            },
        )

    data = {
        "content": gloss.content,
        "language": gloss.language,
        "transcriptions_raw": "\n".join(gloss.transcriptions or []),
        "relations": {
            "contains": list(gloss.contains.all()),
            "near_synonyms": list(gloss.near_synonyms.all()),
            "near_homophones": list(gloss.near_homophones.all()),
            "translations": list(gloss.translations.all()),
            "clarifies_usage": list(gloss.clarifies_usage.all()),
            "to_be_differentiated_from": list(gloss.to_be_differentiated_from.all()),
            "collocations": list(gloss.collocations.all()),
        },
    }
    return render(
        request,
        "cms/gloss_form.html",
        {
            "data": data,
            "errors": [],
            "languages": languages,
            "languages_serialized": languages_serialized,
            "relations_serialized": serialize_relations(data["relations"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "mode": "edit",
            "gloss": gloss,
        },
    )
