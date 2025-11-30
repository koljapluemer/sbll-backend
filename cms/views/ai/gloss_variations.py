from django.shortcuts import render, get_object_or_404, redirect
from cms.models import Gloss
from cms.ai.features.gloss_variations import generate_variations


def gloss_variations(request, pk, num_variations):
    """View to generate and display gloss variations"""
    gloss = get_object_or_404(Gloss, pk=pk)

    result = generate_variations(gloss.content, num_variations)

    return render(request, "cms/gloss_variations.html", {
        "gloss": gloss,
        "num_variations": num_variations,
        "variations": result["variations"],
        "interaction_id": result["interaction_id"],
    })
