from django.urls import path

from accounts.views import AddCheckedView, InQuestionsTrialUsers

urlpatterns = [
    path("api/v0/check_off_link", AddCheckedView.as_view(), name="check_off_content"),
    path(
        "api/v0/questions_trial_users",
        InQuestionsTrialUsers.as_view(),
        name="questions_trial_users",
    ),
]
