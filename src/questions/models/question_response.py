from uuid import uuid4

from django.db import models

from accounts.models import User
from learney_backend.base_models import UUIDModel
from questions.models import QuestionModel


class QuestionResponseModel(UUIDModel):
    user = models.ForeignKey(
        User,
        related_name="question_responses",
        help_text="User whose response this is",
        on_delete=models.CASCADE,
    )
    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.CASCADE,
        help_text="question this was a response to",
        related_name="responses",
    )

    response = models.TextField(max_length=1024, help_text="Response given to the question")
    correct = models.BooleanField(help_text="Was the response correct?")

    time_asked = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question was asked"
    )
    session_id = models.TextField(help_text="session_id of the session the response was from")
    # time_to_respond = models.TimeField(
    #     help_text="Time it took for the user to respond to the question"
    # )
