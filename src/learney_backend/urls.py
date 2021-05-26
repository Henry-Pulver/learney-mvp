from django.urls import path, re_path
from django.shortcuts import render

from learney_web import settings
from learney_backend.views import ContentLinkPreviewView, ContentVoteView


def index(request):
    return render(
        request,
        f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/index.html",
    )


urlpatterns = [
    path("", index, name="index"),
    re_path("api/v0/link_previews", ContentLinkPreviewView.as_view(), name="link previews"),
    re_path("api/v0/votes", ContentVoteView.as_view(), name="votes")
]
