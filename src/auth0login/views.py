from typing import Dict
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout as log_out
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from knowledge_maps.models import KnowledgeMapModel

INDEX_HTML = f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/index.html"
ORIG_MAP_NAME = "original_map"


def get_user_data(auth0user, user) -> Dict[str, str]:
    return {
        "user_id": auth0user.uid,
        "name": user.first_name,
        "picture": auth0user.extra_data["picture"],
        "email": auth0user.extra_data["email"],
    }


def redirect_to_map(request):
    prev_map = request.session.get("previous_map", ORIG_MAP_NAME)
    return redirect(f"/maps/{prev_map}")


def view_map(request, map_name: str = ORIG_MAP_NAME):
    user = request.user
    auth0user = user.social_auth.get(provider="auth0") if user.is_authenticated else ""

    # Update the session
    request.session["previous_map"] = map_name
    map_object = KnowledgeMapModel.objects.get(url_extension=map_name)

    return render(
        request,
        INDEX_HTML,
        {
            "auth0User": auth0user,
            "userdata": get_user_data(auth0user, user) if user.is_authenticated else "",
            "map_uuid": map_object.unique_id,
            "map_version": map_object.version,
            "allow_suggestions": map_object.allow_suggestions,
        },
    )


@login_required
def edit_map(request, map_name: str):
    user = request.user
    auth0user = user.social_auth.get(provider="auth0")

    request.session["previous_map"] = map_name
    map_object = KnowledgeMapModel.objects.get(url_extension=map_name)

    if auth0user.extra_data["email"].lower() == map_object.author_user_id.lower():
        return render(
            request,
            INDEX_HTML,
            {
                "auth0User": auth0user,
                "userdata": get_user_data(auth0user, user) if user.is_authenticated else "",
                "map_uuid": map_object.unique_id,
                "map_version": map_object.version,
                "allow_suggestions": False,
            },
        )
    else:
        # TODO: add an error that says that you aren't the author of this map
        return redirect_to_map(request)


def logout(request):
    log_out(request)
    return_to = urlencode({"returnTo": request.build_absolute_uri("/")})
    logout_url = f"https://{settings.SOCIAL_AUTH_AUTH0_DOMAIN}/v2/logout?client_id={settings.SOCIAL_AUTH_AUTH0_KEY}&{return_to}"
    return HttpResponseRedirect(logout_url)
