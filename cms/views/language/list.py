from django.shortcuts import render

from cms.models import Language


def language_list(request):
    languages = Language.objects.order_by("iso")
    return render(request, "cms/language_list.html", {"languages": languages})
