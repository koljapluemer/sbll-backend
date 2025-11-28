from cms.models import Language


def parse_language_payload(request, instance=None):
    """Parse and validate language form data from request."""
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
