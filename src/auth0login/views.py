import datetime
from typing import Dict
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import logout as log_out
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from knowledge_maps.models import KnowledgeMapModel
from learney_web.settings import DT_STR

INDEX_HTML = f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/index.html"
ORIG_MAP_NAME = "original_map"

SESSION_KEY_CYCLE_TIME = 3600  # secs
SESSION_EXPIRY_TIME = 4 * 7 * 24 * 60 * 60  # 4 weeks in seconds


def get_user_data(request: HttpRequest) -> Dict[str, str]:
    auth0user = (
        request.user.social_auth.get(provider="auth0") if request.user.is_authenticated else None
    )
    return {
        "user_id": auth0user.uid if auth0user is not None else get_anon_user_id(request),
        "name": request.user.first_name if auth0user is not None else "",
        "picture": auth0user.extra_data["picture"] if auth0user is not None else "",
        "email": auth0user.extra_data["email"] if auth0user is not None else "",
    }


def redirect_to_map(request: HttpRequest) -> HttpResponse:
    prev_map = request.session.get("previous_map", ORIG_MAP_NAME)
    return redirect(f"/maps/{prev_map}")


def cycle_session_key_if_old(request: HttpRequest) -> None:
    now = datetime.datetime.utcnow()
    last_action_time = datetime.datetime.strptime(
        request.session.get("last_action", now.strftime(DT_STR)), DT_STR
    )
    time_since_last_action = now - last_action_time
    if time_since_last_action.total_seconds() > SESSION_KEY_CYCLE_TIME:
        request.session.cycle_key()


def get_anon_user_id(request: HttpRequest) -> str:
    return request.session.get("anonymous_user_id", f"anonymous-user|{uuid4()}")


def update_session(request: HttpRequest, map_name: str) -> None:
    cycle_session_key_if_old(request)
    request.session["previous_map"] = map_name
    if request.user.is_anonymous:
        request.session["anonymous_user_id"] = get_anon_user_id(request)
    request.session.set_expiry(SESSION_EXPIRY_TIME)


def view_map(request: HttpRequest, map_name: str = ORIG_MAP_NAME) -> HttpResponse:
    map_object = KnowledgeMapModel.objects.get(url_extension=map_name)
    update_session(request, map_name)

    return render(
        request,
        INDEX_HTML,
        {
            "userdata": get_user_data(request),
            "map_uuid": map_object.unique_id,
            "map_version": map_object.version,
            "allow_suggestions": map_object.allow_suggestions,
        },
    )


@login_required
def edit_map(request, map_name: str) -> HttpResponse:
    map_object = KnowledgeMapModel.objects.get(url_extension=map_name)
    userdata = get_user_data(request)
    update_session(request, map_name)

    if userdata["email"].lower() == map_object.author_user_id.lower():
        return render(
            request,
            INDEX_HTML,
            {
                "userdata": userdata,
                "map_uuid": map_object.unique_id,
                "map_version": map_object.version,
                "allow_suggestions": False,
            },
        )
    else:
        # TODO: add an error that says that you aren't the author of this map
        return redirect_to_map(request)


def logout(request) -> HttpResponse:
    log_out(request)
    return_to = urlencode({"returnTo": request.build_absolute_uri("/")})
    logout_url = f"https://{settings.SOCIAL_AUTH_AUTH0_DOMAIN}/v2/logout?client_id={settings.SOCIAL_AUTH_AUTH0_KEY}&{return_to}"
    return HttpResponseRedirect(logout_url)
