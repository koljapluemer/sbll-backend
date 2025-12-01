from django.shortcuts import render, get_object_or_404
from cms.models import Gloss


def gloss_tools(request, pk):
    """View to show AI tools for a gloss"""
    gloss = get_object_or_404(Gloss, pk=pk)

    return render(request, "cms/gloss_tools.html", {
        "gloss": gloss,
    })
