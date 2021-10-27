from django.shortcuts import render
from django.urls import re_path

from learney_backend.views import ContentLinkPreviewView, ContentVoteView, TotalVoteCountView
from learney_web import settings

HTML_BASE_DIR = f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/"


def render_request(template_name: str):
    return lambda request: render(request, template_name)


urlpatterns = [
    re_path("api/v0/link_previews", ContentLinkPreviewView.as_view(), name="link previews"),
    re_path("api/v0/votes", ContentVoteView.as_view(), name="votes"),
    re_path("api/v0/total_vote_count", TotalVoteCountView.as_view(), name="total vote count"),
]
