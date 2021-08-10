import os
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout as log_out
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

INDEX_HTML = f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/index.html"


def index(request):
    user = request.user
    if user.is_authenticated:
        return redirect(dashboard)
    else:
        return render(
            request,
            INDEX_HTML,
            {"auth0User": "", "userdata": "", "map_name": settings.MAP_NAME},
        )


@login_required
def dashboard(request):
    user = request.user
    auth0user = user.social_auth.get(provider="auth0")

    return render(
        request,
        INDEX_HTML,
        {
            "auth0User": auth0user,
            "userdata": {
                "user_id": auth0user.uid,
                "name": user.first_name,
                "picture": auth0user.extra_data["picture"],
                "email": auth0user.extra_data["email"],
            },
            "map_name": settings.MAP_NAME,
        },
    )


def logout(request):
    log_out(request)
    return_to = urlencode({"returnTo": request.build_absolute_uri("/")})
    logout_url = f"https://{settings.SOCIAL_AUTH_AUTH0_DOMAIN}/v2/logout?client_id={settings.SOCIAL_AUTH_AUTH0_KEY}&{return_to}"
    return HttpResponseRedirect(logout_url)
