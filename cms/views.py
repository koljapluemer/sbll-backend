import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse

from .models import Gloss, Language, Situation


def redirect_home(_request):
    return redirect("language_list")


def language_list(request):
    languages = Language.objects.order_by("iso")
    return render(request, "cms/language_list.html", {"languages": languages})


def _parse_language_payload(request, instance=None):
    errors = []
    iso = request.POST.get("iso", "").strip()
    name = request.POST.get("name", "").strip()
    short = request.POST.get("short", "").strip() or None
    ai_note = request.POST.get("ai_note", "").strip()

    if not instance and not iso:
        errors.append("ISO code is required.")
    if not instance and iso and Language.objects.filter(pk=iso).exists():
        errors.append("A language with this ISO code already exists.")
    if not name:
        errors.append("Name is required.")

    payload = {
        "iso": iso if iso else (instance.iso if instance else ""),
        "name": name,
        "short": short,
        "ai_note": ai_note,
    }
    return payload, errors


def language_create(request):
    initial = {"iso": "", "name": "", "short": "", "ai_note": ""}
    if request.method == "POST":
        payload, errors = _parse_language_payload(request)
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


def language_update(request, pk):
    language = get_object_or_404(Language, pk=pk)
    if request.method == "POST":
        payload, errors = _parse_language_payload(request, instance=language)
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


def language_delete(request, pk):
    language = get_object_or_404(Language, pk=pk)
    if request.method == "POST":
        language.delete()
        return redirect("language_list")
    return render(
        request,
        "cms/language_confirm_delete.html",
        {"language": language},
    )


def gloss_list(request):
    glosses = (
        Gloss.objects.select_related("language")
        .prefetch_related("translations", "near_synonyms")
        .order_by("language__iso", "content")
    )
    return render(request, "cms/gloss_list.html", {"glosses": glosses})


def _gloss_form_payload(request, instance=None):
    errors = []
    content = request.POST.get("content", "").strip()
    language_id = request.POST.get("language", "").strip()
    transcriptions_raw = request.POST.get("transcriptions", "").splitlines()

    if not content:
        errors.append("Content is required.")

    language = None
    if language_id:
        language = Language.objects.filter(pk=language_id).first()
        if not language:
            errors.append("Selected language does not exist.")
    else:
        errors.append("Language is required.")

    transcriptions = [
        line.strip() for line in transcriptions_raw if line.strip()
    ]

    relation_keys = [
        "contains",
        "near_synonyms",
        "near_homophones",
        "translations",
        "clarifies_usage",
        "to_be_differentiated_from",
        "collocations",
    ]
    relations = {}
    for key in relation_keys:
        selected_ids = request.POST.getlist(key)
        if not selected_ids:
            relations[key] = []
            continue
        relations[key] = list(
            Gloss.objects.filter(pk__in=selected_ids).exclude(pk=getattr(instance, "pk", None))
        )

    payload = {
        "content": content,
        "language": language,
        "transcriptions": transcriptions,
        "relations": relations,
        "transcriptions_raw": "\n".join(transcriptions_raw).strip(),
    }
    return payload, errors


def gloss_create(request):
    languages = Language.objects.order_by("name")
    languages_serialized = _serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")
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
        payload, errors = _gloss_form_payload(request)
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
                "languages_serialized": languages_json,
                "relations_serialized": _relations_json(payload["relations"]),
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
            "languages_serialized": languages_json,
            "relations_serialized": _relations_json(empty["relations"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "mode": "create",
        },
    )


def gloss_update(request, pk):
    gloss = get_object_or_404(Gloss, pk=pk)
    languages = Language.objects.order_by("name")
    languages_serialized = _serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")
    if request.method == "POST":
        payload, errors = _gloss_form_payload(request, instance=gloss)
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
                "languages_serialized": languages_json,
                "relations_serialized": _relations_json(payload["relations"]),
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
            "languages_serialized": languages_json,
            "relations_serialized": _relations_json(data["relations"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "mode": "edit",
            "gloss": gloss,
        },
    )


def gloss_delete(request, pk):
    gloss = get_object_or_404(Gloss, pk=pk)
    if request.method == "POST":
        gloss.delete()
        return redirect("gloss_list")
    return render(
        request,
        "cms/gloss_confirm_delete.html",
        {"gloss": gloss},
    )


def situation_list(request):
    situations = Situation.objects.prefetch_related("glosses").order_by("id")
    return render(request, "cms/situation_list.html", {"situations": situations})


def _parse_situation_payload(request, instance=None):
    errors = []
    situation_id = request.POST.get("id", "").strip()
    gloss_ids = request.POST.getlist("glosses")

    if not instance and not situation_id:
        errors.append("ID is required.")
    if not instance and situation_id and Situation.objects.filter(pk=situation_id).exists():
        errors.append("A situation with this ID already exists.")

    glosses = list(Gloss.objects.filter(pk__in=gloss_ids))
    payload = {
        "id": situation_id if situation_id else (instance.id if instance else ""),
        "glosses": glosses,
    }
    return payload, errors


def situation_create(request):
    glosses = Gloss.objects.order_by("content")
    languages = Language.objects.order_by("name")
    languages_serialized = _serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")
    empty = {"id": "", "glosses": []}
    if request.method == "POST":
        payload, errors = _parse_situation_payload(request)
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
                "glosses_serialized": _serialize_glosses(payload["glosses"]),
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
            "glosses_serialized": _serialize_glosses(empty["glosses"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
        },
    )


def situation_update(request, pk):
    situation = get_object_or_404(Situation, pk=pk)
    glosses = Gloss.objects.order_by("content")
    languages = Language.objects.order_by("name")
    languages_serialized = _serialize_languages(languages)
    gloss_search_url = reverse("api_gloss_search")
    gloss_create_url = reverse("api_gloss_create")

    if request.method == "POST":
        payload, errors = _parse_situation_payload(request, instance=situation)
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
                "glosses_serialized": _serialize_glosses(payload["glosses"]),
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
            "glosses_serialized": _serialize_glosses(data["glosses"]),
            "gloss_search_url": gloss_search_url,
            "gloss_create_url": gloss_create_url,
            "situation": situation,
        },
    )


def _serialize_gloss(gloss):
    return {
        "id": gloss.pk,
        "label": f"{gloss.language.iso}: {gloss.content}",
        "content": gloss.content,
        "language_iso": gloss.language.iso,
    }


def _serialize_glosses(glosses):
    return [_serialize_gloss(g) for g in glosses]


def _serialize_relations(relations):
    return {key: _serialize_glosses(items) for key, items in relations.items()}


def _serialize_languages(languages):
    return [
        {
            "id": lang.pk,
            "label": str(lang),
            "iso": lang.iso,
        }
        for lang in languages
    ]


def _relations_json(relations):
    return {key: _serialize_glosses(items) for key, items in relations.items()}


@require_GET
def api_gloss_search(request):
    query = request.GET.get("q", "").strip()
    qs = Gloss.objects.select_related("language")
    if query:
        qs = qs.filter(content__icontains=query)
    results = [_serialize_gloss(gloss) for gloss in qs.order_by("content")[:10]]
    return JsonResponse({"results": results})


@require_POST
def api_gloss_create(request):
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


def situation_delete(request, pk):
    situation = get_object_or_404(Situation, pk=pk)
    if request.method == "POST":
        situation.delete()
        return redirect("situation_list")
    return render(
        request,
        "cms/situation_confirm_delete.html",
        {"situation": situation},
    )

# Create your views here.
