from uuid import uuid4

from django.db import models


class QuestionModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid4, help_text="Unique id for question response"
    )

    question_text = models.TextField(help_text="Text for question")
    answer_text = models.JSONField(
        help_text="JSON list containing answers - first is correct, all after are incorrect."
    )
    feedback_text = models.TextField(help_text="Text containing feedback")

    author_user_id = models.CharField(
        max_length=64, help_text="User ID of user who wrote this question"
    )
    session_id = models.TextField(
        null=True, blank=True, help_text="session_id of the session the question was written in"
    )
    time_written = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question was written"
    )
