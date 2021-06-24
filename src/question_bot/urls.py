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

from question_bot.views import FeedbackView, QuestionsView, QuestionUserView

urlpatterns = [
    path("api/v0/feedback", FeedbackView.as_view(), name="feedback"),
    path("api/v0/questions", QuestionsView.as_view(), name="questions"),
    path("api/v0/add_user", QuestionUserView.as_view(), name="question_users"),
]
