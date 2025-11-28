from cms.models import Gloss, Language


def parse_gloss_form_payload(request, instance=None):
    """Parse and validate gloss form data from request."""
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


def serialize_gloss(gloss):
    """Serialize a gloss object to a dictionary."""
    return {
        "id": gloss.pk,
        "label": f"{gloss.language.iso}: {gloss.content}",
        "content": gloss.content,
        "language_iso": gloss.language.iso,
    }


def serialize_glosses(glosses):
    """Serialize a list of gloss objects."""
    return [serialize_gloss(g) for g in glosses]


def serialize_relations(relations):
    """Serialize relations dictionary."""
    return {key: serialize_glosses(items) for key, items in relations.items()}
