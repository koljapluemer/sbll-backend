from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db import transaction
from urllib.parse import quote
import json
from cms.models import Gloss, Language
from cms.ai.features.gloss_example_sentences import generate_example_sentences


def gloss_example_sentences(request, pk, num_sentences):
    """View to generate, display, and save example sentences for a gloss"""
    gloss = get_object_or_404(Gloss, pk=pk)

    if request.method == "POST":
        # Check if this is language selection or sentence confirmation
        if "translation_language" in request.POST:
            # Language selection submission → generate sentences
            translation_iso = request.POST.get("translation_language", "").strip()

            # Handle "no translation" case
            if translation_iso == "__none__" or not translation_iso:
                translation_language = None
                save_language = gloss.language
            else:
                translation_language = get_object_or_404(Language, iso=translation_iso)
                save_language = translation_language

            # Generate sentences
            result = generate_example_sentences(
                gloss.content,
                gloss.language,
                translation_language,
                num_sentences
            )

            # Render results page
            return render(request, "cms/gloss_example_sentences.html", {
                "gloss": gloss,
                "num_sentences": num_sentences,
                "sentences": result["sentences"],
                "sentences_json": json.dumps(result["sentences"]),
                "save_language": save_language,
                "source_language": gloss.language,
                "has_translation": translation_language is not None,
                "interaction_id": result["interaction_id"],
            })

        else:
            # Sentence confirmation submission → save selected
            selected_indices = request.POST.getlist("selected_sentences")
            save_language_iso = request.POST.get("save_language_iso")
            source_language_iso = request.POST.get("source_language_iso")
            has_translation = request.POST.get("has_translation") == "true"

            # Parse sentence pairs from hidden inputs
            sentences_json = request.POST.get("sentences_data")
            sentences = json.loads(sentences_json) if sentences_json else []

            if not selected_indices:
                # Re-render with error - redirect back to language selection
                return redirect(f"{reverse('gloss_example_sentences_select_language', args=[pk, num_sentences])}?toast={quote('Please select at least one sentence')}&toast_type=error")

            save_language = get_object_or_404(Language, iso=save_language_iso)
            source_language = get_object_or_404(Language, iso=source_language_iso)

            created_count = 0
            linked_count = 0

            with transaction.atomic():
                for idx_str in selected_indices:
                    idx = int(idx_str)
                    sentence = sentences[idx]

                    if has_translation and sentence.get("translation"):
                        # Create both original and translation glosses
                        original_gloss, original_created = Gloss.objects.get_or_create(
                            content=sentence["original"],
                            language=source_language,
                            defaults={'transcriptions': []}
                        )

                        translated_gloss, translated_created = Gloss.objects.get_or_create(
                            content=sentence["translation"],
                            language=save_language,
                            defaults={'transcriptions': []}
                        )

                        if original_created:
                            created_count += 1
                        if translated_created:
                            created_count += 1

                        # Link original and translation as translations
                        original_gloss.translations.add(translated_gloss)

                        # Link both to original gloss via clarifies_usage
                        original_gloss.clarifies_usage.add(gloss)
                        translated_gloss.clarifies_usage.add(gloss)
                        linked_count += 2
                    else:
                        # No translation, just create the original sentence
                        sentence_gloss, created = Gloss.objects.get_or_create(
                            content=sentence["original"],
                            language=source_language,
                            defaults={'transcriptions': []}
                        )

                        if created:
                            created_count += 1

                        # Link to original gloss via clarifies_usage
                        sentence_gloss.clarifies_usage.add(gloss)
                        linked_count += 1

            # Success message
            if created_count > 0 and linked_count > created_count:
                message = f"Created {created_count} example sentence(s) and linked {linked_count} total"
            elif created_count > 0:
                message = f"Created {created_count} example sentence(s) linked to gloss"
            else:
                message = f"Linked {linked_count} existing sentence(s) to gloss"

            return redirect(f"{reverse('gloss_list')}?toast={quote(message)}&toast_type=success")

    # GET: redirect to language selection
    return redirect(reverse('gloss_example_sentences_select_language', args=[pk, num_sentences]))
