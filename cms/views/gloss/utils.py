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

    PHASE 1: Uses breadth-first search (BFS) to traverse gloss relationships:
    1. Start with glosses from situation.glosses.all()
    2. Track visited glosses by compound key to prevent cycles
    3. For each gloss:
       - Process 'contains' relationships: include contained glosses only if they are
         in the native or target language (apply recursively)
       - Process 'translations' relationships:
         * For glosses in native language: include only translations in target language
         * For glosses in target language: include only translations in native language

    PHASE 2: Collect additional relationships at 1.5 depth:
    For each gloss from Phase 1:
       - Process relationship fields: near_synonyms, near_homophones, clarifies_usage,
         to_be_differentiated_from, collocations
       - Include related glosses (Level 1 - assumed same language as source)
       - Include translations of related glosses in the "other" language (Level 1.5)
       - Process "examples" (reverse clarifies_usage) with same pattern
       - No further recursion beyond 1.5 depth

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

    # PHASE 2: Collect related glosses at 1.5 depth
    # Create a snapshot of current glosses to iterate over (avoid modifying during iteration)
    phase1_glosses = list(result_glosses)

    # Track glosses to add (will be added to result_glosses at the end)
    additional_glosses = {}  # Use dict to deduplicate by compound_key

    # Relationship fields to process
    relationship_fields = [
        'near_synonyms',
        'near_homophones',
        'clarifies_usage',
        'to_be_differentiated_from',
        'collocations',
    ]

    for current_gloss in phase1_glosses:
        current_language = current_gloss.language.iso

        # Determine "other language"
        if current_language == native_language_iso:
            other_language_iso = target_language_iso
        elif current_language == target_language_iso:
            other_language_iso = native_language_iso
        else:
            # Gloss is in neither language, skip
            continue

        # Process each relationship field
        for field_name in relationship_fields:
            related_glosses = getattr(current_gloss, field_name).select_related('language').all()

            for related_gloss in related_glosses:
                # Level 1: Add the related gloss (assume same language)
                rel_key = related_gloss.get_compound_key()
                if rel_key not in visited_keys and rel_key not in additional_glosses:
                    additional_glosses[rel_key] = related_gloss
                    visited_keys.add(rel_key)

                # Level 1.5: Add translations of related gloss in other language
                for translation in related_gloss.translations.select_related('language').all():
                    if translation.language.iso == other_language_iso:
                        trans_key = translation.get_compound_key()
                        if trans_key not in visited_keys and trans_key not in additional_glosses:
                            additional_glosses[trans_key] = translation
                            visited_keys.add(trans_key)

        # Handle "examples" (reverse clarifies_usage)
        example_glosses = current_gloss.usage_of_clarified.select_related('language').all()
        for example_gloss in example_glosses:
            # Level 1: Add the example gloss
            ex_key = example_gloss.get_compound_key()
            if ex_key not in visited_keys and ex_key not in additional_glosses:
                additional_glosses[ex_key] = example_gloss
                visited_keys.add(ex_key)

            # Level 1.5: Add translations of example gloss in other language
            for translation in example_gloss.translations.select_related('language').all():
                if translation.language.iso == other_language_iso:
                    trans_key = translation.get_compound_key()
                    if trans_key not in visited_keys and trans_key not in additional_glosses:
                        additional_glosses[trans_key] = translation
                        visited_keys.add(trans_key)

    # Add all additional glosses to result
    result_glosses.extend(additional_glosses.values())

    return result_glosses


def serialize_gloss_to_json(gloss):
    """
    Serialize a gloss to a dictionary suitable for standalone JSON export.

    Includes all data and relationships without filtering.

    Args:
        gloss: Gloss instance with prefetched relationships

    Returns:
        Dictionary with complete gloss data
    """
    # Helper function to extract all keys (no filtering)
    def get_all_keys(relationship_queryset):
        return [g.get_compound_key() for g in relationship_queryset.all()]

    return {
        "key": gloss.get_compound_key(),
        "content": gloss.content,
        "language": gloss.language.iso,
        "transcriptions": gloss.transcriptions,
        "contains": get_all_keys(gloss.contains),
        "translations": get_all_keys(gloss.translations),
        "near_synonyms": get_all_keys(gloss.near_synonyms),
        "near_homophones": get_all_keys(gloss.near_homophones),
        "clarifies_usage": get_all_keys(gloss.clarifies_usage),
        "to_be_differentiated_from": get_all_keys(gloss.to_be_differentiated_from),
        "collocations": get_all_keys(gloss.collocations),
        "examples": get_all_keys(gloss.usage_of_clarified),
    }


def serialize_gloss_to_jsonl(gloss, target_language_iso=None):
    """
    Serialize a gloss to a dictionary suitable for JSONL export.

    Uses compound keys for cross-referencing instead of internal IDs.

    Args:
        gloss: Gloss instance with prefetched relationships
        target_language_iso: Optional ISO code of target language. If provided,
                           paraphrased glosses in this language will be filtered
                           from all relationship fields.

    Returns:
        Dictionary with gloss data including all relationship fields
    """

    # Helper function to extract and filter keys
    def get_filtered_keys(relationship_queryset):
        glosses = relationship_queryset.all()
        if target_language_iso:
            return [
                g.get_compound_key() for g in glosses
                if not (g.language.iso == target_language_iso and g.is_paraphrased())
            ]
        else:
            return [g.get_compound_key() for g in glosses]

    # Existing relationships
    contains_keys = get_filtered_keys(gloss.contains)
    translation_keys = get_filtered_keys(gloss.translations)

    # New relationships
    near_synonyms_keys = get_filtered_keys(gloss.near_synonyms)
    near_homophones_keys = get_filtered_keys(gloss.near_homophones)
    clarifies_usage_keys = get_filtered_keys(gloss.clarifies_usage)
    to_be_differentiated_from_keys = get_filtered_keys(gloss.to_be_differentiated_from)
    collocations_keys = get_filtered_keys(gloss.collocations)

    # Examples (reverse clarifies_usage)
    examples_keys = get_filtered_keys(gloss.usage_of_clarified)

    return {
        "key": gloss.get_compound_key(),
        "content": gloss.content,
        "language": gloss.language.iso,
        "transcriptions": gloss.transcriptions,
        "contains": contains_keys,
        "translations": translation_keys,
        "near_synonyms": near_synonyms_keys,
        "near_homophones": near_homophones_keys,
        "clarifies_usage": clarifies_usage_keys,
        "to_be_differentiated_from": to_be_differentiated_from_keys,
        "collocations": collocations_keys,
        "examples": examples_keys,
    }
