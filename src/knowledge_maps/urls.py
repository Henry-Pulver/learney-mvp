from django.urls import path

from knowledge_maps.views import KnowledgeMapView

urlpatterns = [
    path("api/v0/knowledge_maps", KnowledgeMapView.as_view(), name="knowledge_maps"),
]
