from uuid import uuid4

from django.db import models

from learney_backend.models import UUIDModel
from questions.models import QuestionTemplateModel
from questions.validators import ensure_list, integer_is_positive, not_null


class QuestionModel(UUIDModel):
    template_used = models.ForeignKey(
        QuestionTemplateModel, on_delete=models.CASCADE, related_name="question_instances"
    )
    difficulty = models.FloatField(
        help_text="Question difficulty for the concept. Initially set by an expert, but will subsequently be inferred from data. A relative scale, with 0 the lowest possible and as many difficulty levels as is deemed makes sense by the expert.",
        validators=[integer_is_positive],
    )

    question_text = models.TextField(
        help_text="Text for question", blank=False, validators=[not_null]
    )
    answer_text = models.JSONField(
        help_text="JSON list containing answers - first is correct, all after are incorrect.",
        blank=False,
        validators=[not_null, ensure_list],
    )
    feedback_text = models.TextField(
        help_text="Text containing feedback", blank=False, validators=[not_null]
    )
