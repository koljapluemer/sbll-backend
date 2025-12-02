from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from urllib.parse import quote

from cms.models import Gloss, Language
from cms.ai.features.gloss_translation import generate_translations


@require_http_methods(["GET", "POST"])
def tools_translate_glosses(request):
    """Generate and review AI translations for selected glosses."""

    if request.method == "POST":
        # Check if this is the initial translation request or acceptance
        if "gloss_ids" in request.POST:
            # Initial request: generate translations
            gloss_ids = request.POST.getlist("gloss_ids")
            native_iso = request.POST.get("native", "").strip()
            target_iso = request.POST.get("lang", "").strip()

            if not gloss_ids:
                return redirect(f"{reverse('tools_untranslated_glosses')}?native={native_iso}&lang={target_iso}&toast={quote('Please select at least one gloss')}&toast_type=error")

            # Fetch glosses and languages
            glosses = list(Gloss.objects.filter(id__in=gloss_ids).select_related("language"))
            target_language = get_object_or_404(Language, iso=target_iso)

            if not glosses:
                return redirect(f"{reverse('tools_untranslated_glosses')}?native={native_iso}&lang={target_iso}")

            # Generate translations
            result = generate_translations(glosses, target_language)

            # Store in session for the review page
            request.session['translation_data'] = {
                "translations": result["translations"],
                "native_iso": native_iso,
                "target_iso": target_iso,
                "interaction_id": result["interaction_id"],
            }

            return render(request, "cms/tools_translate_glosses.html", {
                "translations": result["translations"],
                "native_iso": native_iso,
                "target_iso": target_iso,
                "target_language": target_language,
            })

        else:
            # Acceptance: create glosses and relationships
            selected = request.POST.getlist("selected_translations")
            translation_data = request.session.get('translation_data')

            if not translation_data:
                return redirect(reverse('tools_untranslated_glosses'))

            if not selected:
                # Re-render with error
                target_language = get_object_or_404(Language, iso=translation_data["target_iso"])
                return render(request, "cms/tools_translate_glosses.html", {
                    "translations": translation_data["translations"],
                    "native_iso": translation_data["native_iso"],
                    "target_iso": translation_data["target_iso"],
                    "target_language": target_language,
                    "error": "Please select at least one translation to save.",
                })

            # Parse selected translations (format: "source_id:translation_text")
            native_iso = translation_data["native_iso"]
            target_iso = translation_data["target_iso"]
            target_language = get_object_or_404(Language, iso=target_iso)

            created_count = 0
            linked_count = 0

            with transaction.atomic():
                for item in selected:
                    source_id, translation_text = item.split(":", 1)
                    source_gloss = get_object_or_404(Gloss, id=int(source_id))

                    # Create or get target gloss
                    target_gloss, created = Gloss.objects.get_or_create(
                        content=translation_text,
                        language=target_language,
                        defaults={'transcriptions': []}
                    )

                    if created:
                        created_count += 1

                    # Establish mutual translation relationship
                    source_gloss.translations.add(target_gloss)
                    linked_count += 1

            # Clear session data
            del request.session['translation_data']

            # Build success message
            if created_count > 0:
                message = f"Created {created_count} translation(s) and linked {linked_count} gloss pair(s)"
            else:
                message = f"Linked {linked_count} existing translation(s)"

            return redirect(f"{reverse('tools_untranslated_glosses')}?native={native_iso}&lang={target_iso}&toast={quote(message)}&toast_type=success")

    # GET request: redirect to search page
    return redirect(reverse('tools_untranslated_glosses'))
