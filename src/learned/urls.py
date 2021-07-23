from django.urls import path

from learned.views import LearnedView

urlpatterns = [
    path("api/v0/learned", LearnedView.as_view(), name="learned"),
]
