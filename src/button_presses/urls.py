from django.urls import path

from button_presses.views import ButtonPressView

urlpatterns = [
    path("api/v0/button_press", ButtonPressView.as_view(), name="Button Press"),
]
