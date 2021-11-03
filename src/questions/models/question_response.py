from uuid import uuid4

from django.db import models


class QuestionResponseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid4, help_text="Unique id for question response"
    )
    user_id = models.CharField(max_length=64, help_text="User ID of user whose response this is")
    session_id = models.TextField(help_text="session_id of the session the response was from")
    question_id = models.UUIDField(help_text="id of the question this was a response to")

    response = models.TextField(max_length=1024, help_text="Response to this question")
    correct = models.BooleanField(help_text="Was response correct?")

    time_to_respond = models.TimeField(
        help_text="Time it took for the user to respond to the question"
    )
    time_asked = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question was asked"
    )
