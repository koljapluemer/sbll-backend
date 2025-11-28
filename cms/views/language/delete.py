from django.shortcuts import get_object_or_404, redirect, render

from cms.models import Language


def language_delete(request, pk):
    language = get_object_or_404(Language, pk=pk)
    if request.method == "POST":
        language.delete()
        return redirect("language_list")
    return render(
        request,
        "cms/language_confirm_delete.html",
        {"language": language},
    )
