from django.db import models

from accounts.models import User
from learney_backend.base_models import UUIDModel


class QuestionSet(UUIDModel):
    user = models.ForeignKey(
        User,
        related_name="question_responses",
        help_text="User whose response this is",
        on_delete=models.CASCADE,
    )

    time_started = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question set was started"
    )
    time_taken_to_complete = models.DateTimeField(
        null=True,
        default=None,
        help_text="Time after the question set was started that it was completed",
    )
    completed = models.BooleanField(
        default=False, help_text="Whether the user answered all the questions in the set or not"
    )
    level_at_start = models.IntegerField(
        help_text="The concept level the user started the question set at"
    )
    levels_progressed = models.IntegerField(
        default=0, help_text="How many levels the user progressed in this question batch"
    )
    concept_completed = models.BooleanField(
        default=False,
        help_text="Whether the highest level of the concept was achieved in this question set",
    )
    session_id = models.TextField(help_text="session_id of the session the response was from")
