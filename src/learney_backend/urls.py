from django.shortcuts import render
from django.urls import path, re_path

from auth0login.views import redirect_to_map, view_map
from learney_backend.views import ContentLinkPreviewView, ContentVoteView
from learney_web import settings

HTML_BASE_DIR = f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/"


def render_request(template_name: str):
    return lambda request: render(request, template_name)


urlpatterns = [
    path("", view_map, name="index"),
    path("dashboard", redirect_to_map),
    path(
        "2021/05/26/privacy_policy",
        render_request(f"{HTML_BASE_DIR}/privacy_policy.html"),
        name="privacy_policy",
    ),
    path(
        "2021/05/26/terms_of_use",
        render_request(f"{HTML_BASE_DIR}/terms_of_use.html"),
        name="terms_of_use",
    ),
    re_path("api/v0/link_previews", ContentLinkPreviewView.as_view(), name="link previews"),
    re_path("api/v0/votes", ContentVoteView.as_view(), name="votes"),
]
