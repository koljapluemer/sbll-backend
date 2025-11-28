from django.shortcuts import get_object_or_404, redirect, render

from cms.models import Situation


def situation_delete(request, pk):
    situation = get_object_or_404(Situation, pk=pk)
    if request.method == "POST":
        situation.delete()
        return redirect("situation_list")
    return render(
        request,
        "cms/situation_confirm_delete.html",
        {"situation": situation},
    )
