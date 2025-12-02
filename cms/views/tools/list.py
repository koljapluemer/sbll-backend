from django.shortcuts import render


def tools_list(request):
    """Landing page listing all available tools."""
    return render(request, "cms/tools_list.html")
