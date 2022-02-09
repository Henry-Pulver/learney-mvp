from typing import Any, Dict

from django.db import models
from django.db.models import CheckConstraint

from accounts.models import User
from learney_backend.base_models import UUIDModel
from questions.models.question_batch import QuestionBatch
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
    question_batch = models.ForeignKey(
        QuestionBatch,
        on_delete=models.CASCADE,
        related_name="responses",
        help_text="The question batch this question corresponds to",
    )

    response = models.TextField(
        max_length=1024,
        null=True,
        default=None,
        help_text="Response given to the question. Null if yet to be answered",
    )
    predicted_prob_correct = models.FloatField(
        help_text="Predicted probability of answer being correct prior to answering"
    )
    correct = models.BooleanField(
        default=None, null=True, help_text="Was the response correct? Null if not yet answered."
    )

    session_id = models.TextField(help_text="session_id of the session the response was from")
    time_to_respond = models.DurationField(
        null=True,
        help_text="Time it took for the user to respond to the question. Measured on the backend. Currently measured, but not used",
    )
    time_asked = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question was asked"
    )

    @property
    def json(self) -> Dict[str, Any]:
        return self.question_template.to_question_json(self.id, self.question_params)

    class Meta:
        constraints = [
            CheckConstraint(
                check=models.Q(predicted_prob_correct__gte=0)
                & models.Q(predicted_prob_correct__lte=1),
                name="prob_correct_is_valid_probability",
            )
        ]
