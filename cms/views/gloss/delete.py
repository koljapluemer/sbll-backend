from django.shortcuts import get_object_or_404, redirect, render

from cms.models import Gloss


def gloss_delete(request, pk):
    gloss = get_object_or_404(Gloss, pk=pk)
    if request.method == "POST":
        gloss.delete()
        return redirect("gloss_list")
    return render(
        request,
        "cms/gloss_confirm_delete.html",
        {"gloss": gloss},
    )
