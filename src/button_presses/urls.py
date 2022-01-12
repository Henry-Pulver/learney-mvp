from django.urls import path

from button_presses.views import ButtonPressView, MapEventTrackingView

urlpatterns = [
    path("api/v0/button_press", ButtonPressView.as_view(), name="Button Press"),
    path("api/v0/cytoscape_events", MapEventTrackingView.as_view(), name="Cytoscape Events"),
]
