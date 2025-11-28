"""Shared utility functions used across multiple view modules."""


def serialize_languages(languages):
    """Serialize a list of Language objects for JSON responses."""
    return [
        {
            "id": lang.pk,
            "label": str(lang),
            "iso": lang.iso,
        }
        for lang in languages
    ]
