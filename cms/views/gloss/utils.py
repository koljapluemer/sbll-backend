from collections import deque
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


def collect_glosses_recursively(situation, native_language_iso, target_language_iso):
    """
    Recursively collect all relevant glosses for a situation based on language filters.

    Algorithm uses breadth-first search (BFS) to traverse gloss relationships:
    1. Start with glosses from situation.glosses.all()
    2. Track visited glosses by compound key to prevent cycles
    3. For each gloss:
       - Process 'contains' relationships: include contained glosses only if they are
         in the native or target language (apply recursively)
       - Process 'translations' relationships:
         * For glosses in native language: include only translations in target language
         * For glosses in target language: include only translations in native language

    Args:
        situation: Situation instance
        native_language_iso: ISO code of native language (str)
        target_language_iso: ISO code of target language (str)

    Returns:
        List of Gloss objects
    """
    # Use sets for O(1) lookup performance
    visited_keys = set()
    result_glosses = []

    # BFS queue: stores tuples of (gloss, depth) for debugging/optimization potential
    queue = deque()

    # Start with all glosses directly associated with the situation
    # Use select_related to avoid N+1 queries when accessing language
    # Use prefetch_related to efficiently load relationships
    initial_glosses = situation.glosses.select_related('language').prefetch_related(
        'contains__language',
        'translations__language'
    ).all()

    for gloss in initial_glosses:
        queue.append(gloss)

    while queue:
        current_gloss = queue.popleft()

        # Get compound key for cycle detection
        compound_key = current_gloss.get_compound_key()

        # Skip if already visited (prevents infinite loops in circular relationships)
        if compound_key in visited_keys:
            continue

        # Mark as visited and add to results
        visited_keys.add(compound_key)
        result_glosses.append(current_gloss)

        current_language = current_gloss.language.iso

        # Process 'contains' relationships
        # Rule: Include contained glosses only if they are in native or target language
        for contained_gloss in current_gloss.contains.select_related('language').all():
            contained_language = contained_gloss.language.iso

            # Filter: only include if in native or target language
            if contained_language in (native_language_iso, target_language_iso):
                if contained_gloss.get_compound_key() not in visited_keys:
                    queue.append(contained_gloss)

        # Process 'translations' relationships
        # Rule: For native language glosses, fetch target language translations
        #       For target language glosses, fetch native language translations
        for translation in current_gloss.translations.select_related('language').all():
            translation_language = translation.language.iso

            # Filter based on current gloss language
            should_include = False
            if current_language == native_language_iso:
                # Current gloss is in native language: include only target language translations
                should_include = translation_language == target_language_iso
            elif current_language == target_language_iso:
                # Current gloss is in target language: include only native language translations
                should_include = translation_language == native_language_iso

            if should_include and translation.get_compound_key() not in visited_keys:
                queue.append(translation)

    return result_glosses


def serialize_gloss_to_jsonl(gloss):
    """
    Serialize a gloss to a dictionary suitable for JSONL export.

    Uses compound keys for cross-referencing instead of internal IDs.

    Args:
        gloss: Gloss instance with prefetched relationships

    Returns:
        Dictionary with gloss data
    """
    # Get related notes
    notes = []
    for note in gloss.note_set.all():
        notes.append({
            "type": note.note_type,
            "content": note.content,
            "show_before_solution": note.show_before_solution,
        })

    # Get compound keys for all related glosses
    contains_keys = [g.get_compound_key() for g in gloss.contains.all()]
    translation_keys = [g.get_compound_key() for g in gloss.translations.all()]

    return {
        "key": gloss.get_compound_key(),
        "content": gloss.content,
        "language": gloss.language.iso,
        "transcriptions": gloss.transcriptions,
        "contains": contains_keys,
        "translations": translation_keys,
        "notes": notes,
    }
