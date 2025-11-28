from cms.models import Gloss, Situation


def parse_situation_payload(request, instance=None):
    """Parse and validate situation form data from request."""
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


def serialize_glosses(glosses):
    """Serialize a list of glosses for situations."""
    return [
        {
            "id": gloss.pk,
            "label": f"{gloss.language.iso}: {gloss.content}",
            "content": gloss.content,
            "language_iso": gloss.language.iso,
        }
        for gloss in glosses
    ]
