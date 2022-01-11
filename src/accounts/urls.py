from django.urls import path

from accounts.views import AddCheckedView

urlpatterns = [
    path("api/v0/check_off_link", AddCheckedView.as_view(), name="check_off_content"),
]
