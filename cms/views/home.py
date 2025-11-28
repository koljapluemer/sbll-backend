from django.shortcuts import redirect


def redirect_home(_request):
    """Redirect home page to language list."""
    return redirect("language_list")
