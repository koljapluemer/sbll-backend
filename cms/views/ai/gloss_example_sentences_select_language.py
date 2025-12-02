from django.shortcuts import render, get_object_or_404
from cms.models import Gloss, Language


def gloss_example_sentences_select_language(request, pk, num_sentences):
    """Language selection page before generating example sentences"""
    gloss = get_object_or_404(Gloss, pk=pk)
    languages = Language.objects.all().order_by("name")

    return render(request, "cms/gloss_example_sentences_select_language.html", {
        "gloss": gloss,
        "num_sentences": num_sentences,
        "languages": languages,
    })
