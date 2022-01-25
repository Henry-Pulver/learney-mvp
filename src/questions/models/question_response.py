from django.db import models

from accounts.models import User
from learney_backend.base_models import UUIDModel
from questions.models.question_set import QuestionSet
from questions.models.question_template import QuestionTemplate


class QuestionResponse(UUIDModel):
    user = models.ForeignKey(
        User,
        related_name="responses",
        help_text="User whose response this is",
        on_delete=models.CASCADE,
    )
    question_template = models.ForeignKey(
        QuestionTemplate,
        on_delete=models.CASCADE,
        help_text="question template this was a response to",
        related_name="responses",
    )
    question_params = models.JSONField(
        help_text="question parameter values chosen from the template parameters",
    )

    response = models.TextField(
        max_length=1024,
        null=True,
        help_text="Response given to the question. Null if yet to be answered",
    )
    correct = models.BooleanField(
        null=True, help_text="Was the response correct? Null if not yet answered."
    )

    question_set = models.ForeignKey(
        QuestionSet,
        on_delete=models.CASCADE,
        related_name="responses",
        help_text="The question set this question corresponds to",
    )
    session_id = models.TextField(help_text="session_id of the session the response was from")
    time_to_respond = models.TimeField(
        null=True,
        help_text="Time it took for the user to respond to the question. Measured on the backend",
    )
    time_asked = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question was asked"
    )
