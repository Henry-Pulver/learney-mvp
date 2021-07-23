from django.urls import include, path

from auth0login import views

urlpatterns = [
    path("dashboard", views.dashboard),
    path("logout", views.logout),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
]
