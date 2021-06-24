from django.urls import path

from link_clicks.views import LinkClickView

urlpatterns = [
    path("api/v0/link_click", LinkClickView.as_view(), name="link_click"),
]
