"""question_bot URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from questions.views import (
    ConceptInfoView,
    CurrentConceptView,
    QuestionBatchView,
    QuestionResponseView,
    QuestionView,
    ReportBrokenQuestionView,
)

urlpatterns = [
    path("api/v0/concept_info", ConceptInfoView.as_view(), name="concept_info"),
    path("api/v0/current_concept", CurrentConceptView.as_view(), name="next_concept"),
    path("api/v0/question_batch", QuestionBatchView.as_view(), name="question_batch"),
    path("api/v0/questions", QuestionView.as_view(), name="questions"),
    path("api/v0/question_response", QuestionResponseView.as_view(), name="question_responses"),
    path(
        "api/v0/report_broken_question",
        ReportBrokenQuestionView.as_view(),
        name="report_broken_questions",
    ),
]
