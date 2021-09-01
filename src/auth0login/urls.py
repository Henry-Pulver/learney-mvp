from django.urls import include, path

from auth0login.views import edit_map, logout, view_map

urlpatterns = [
    path("maps/edit/<str:map_name>", edit_map),
    path("maps/<str:map_name>", view_map),
    path("logout", logout),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
]
