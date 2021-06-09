from django.urls import path
from goals.views import GoalView


urlpatterns = [
    path('api/v0/goals', GoalView.as_view(), name="goals"),
]
