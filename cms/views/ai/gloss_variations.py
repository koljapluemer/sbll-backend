from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db import transaction
from urllib.parse import quote
from cms.models import Gloss
from cms.ai.features.gloss_variations import generate_variations


def gloss_variations(request, pk, num_variations):
    """View to generate, display, and save gloss variations"""
    gloss = get_object_or_404(Gloss, pk=pk)

    if request.method == "POST":
        selected_variations = request.POST.getlist("selected_variations")

        if not selected_variations:
            result = generate_variations(gloss.content, gloss.language, num_variations)
            return render(request, "cms/gloss_variations.html", {
                "gloss": gloss,
                "num_variations": num_variations,
                "variations": result["variations"],
                "interaction_id": result["interaction_id"],
                "error": "Please select at least one variation to save.",
            })

        created_count = 0
        linked_count = 0

        with transaction.atomic():
            for variation_content in selected_variations:
                new_gloss, created = Gloss.objects.get_or_create(
                    content=variation_content,
                    language=gloss.language,
                    defaults={'transcriptions': []}
                )

                if created:
                    created_count += 1

                gloss.near_synonyms.add(new_gloss)
                linked_count += 1

        if created_count > 0 and linked_count > created_count:
            message = f"Created {created_count} new variation(s) and linked {linked_count} variation(s) as near synonyms"
        elif created_count > 0:
            message = f"Created {created_count} variation(s) and linked as near synonyms"
        else:
            message = f"Linked {linked_count} existing variation(s) as near synonyms"

        return redirect(f"{reverse('gloss_list')}?toast={quote(message)}&toast_type=success")

    result = generate_variations(gloss.content, gloss.language, num_variations)

    return render(request, "cms/gloss_variations.html", {
        "gloss": gloss,
        "num_variations": num_variations,
        "variations": result["variations"],
        "interaction_id": result["interaction_id"],
    })
