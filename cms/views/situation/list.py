from django.shortcuts import render

from cms.models import Situation


def situation_list(request):
    situations = Situation.objects.prefetch_related("glosses").order_by("id")
    return render(request, "cms/situation_list.html", {"situations": situations})
