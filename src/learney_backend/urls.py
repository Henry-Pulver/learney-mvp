from django.urls import path, re_path
from learney_backend.views import ContentLinkPreviewView, ContentVoteView

from django.shortcuts import render
import os


def index(request):
    return render(
        request,
        f"{os.path.dirname(os.getcwd())}/src/learney_backend/templates/learney_backend/index.html",
    )


urlpatterns = [
    path("", index, name="index"),
    re_path("api/v0/link_previews", ContentLinkPreviewView.as_view(), name="link previews"),
    re_path("api/v0/votes", ContentVoteView.as_view(), name="votes")
]
