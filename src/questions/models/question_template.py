from django.db import models

from knowledge_maps.models import Concept
from learney_backend.base_models import UUIDModel
from questions.validators import integer_is_positive, not_null


class QuestionTemplate(UUIDModel):
    concept = models.ForeignKey(
        Concept,
        related_name="question_templates",
        help_text="Concept that the question corresponds to",
        on_delete=models.CASCADE,
    )
    difficulty = models.FloatField(
        help_text="Question difficulty for the concept. Initially set by an expert, but will "
        "subsequently be inferred from data. A relative scale, with 0 the lowest "
        "possible and as many difficulty levels as is deemed makes sense by the expert.",
        validators=[integer_is_positive],
    )
    question_type = models.TextField(
        help_text="Text for question template - generates full question",
        blank=False,
        validators=[not_null],
    )

    template_text = models.TextField(
        help_text="Text for question template - generates full question",
        blank=False,
        validators=[not_null],
        max_length=16384,
    )
    correct_answer_letter = models.CharField(
        max_length=1,
        help_text="Answer option (a, b, c or d) which is the correct answer to the question",
        blank=False,
    )
    active = models.BooleanField(
        default=False,
        help_text="If questions from the template should be used onthe live site - "
        "broken questions should be deactivated until they're fixed!",
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(correct_answer__in=["a", "A", "b", "B", "c", "C", "d", "D"]),
                name="correct_answer_letter",
            )
        ]
