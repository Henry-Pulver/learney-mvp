from django.urls import path

from page_visits.views import PageVisitView

urlpatterns = [
    path("api/v0/page_visit", PageVisitView.as_view(), name="page_visit"),
]
