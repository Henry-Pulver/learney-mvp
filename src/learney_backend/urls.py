from django.urls import path, re_path
from django.shortcuts import render

from learney_web import settings
from learney_backend.views import ContentLinkPreviewView, ContentVoteView


def index(request):
    return render(
        request,
        f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/index.html",
        {"auth0User": "",
         "userdata": ""},
    )


def privacy_policy(request):
    return render(
        request,
        f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/privacy_policy.html",
    )


def terms_of_use(request):
    return render(
        request,
        f"{settings.BASE_DIR}/learney_backend/templates/learney_backend/terms_of_use.html",
    )


urlpatterns = [
    path("", index, name="index"),
    path("2021/05/26/privacy_policy", privacy_policy, name="privacy_policy"),
    path("2021/05/26/terms_of_use", terms_of_use, name="terms_of_use"),
    re_path("api/v0/link_previews", ContentLinkPreviewView.as_view(), name="link previews"),
    re_path("api/v0/votes", ContentVoteView.as_view(), name="votes")
]
