from django.db import models

from knowledge_maps.models import Concept
from learney_backend.base_models import UUIDModel
from questions.validators import integer_is_positive, not_null


class QuestionTemplateModel(UUIDModel):
    concept = models.ForeignKey(
        Concept,
        related_name="question_templates",
        help_text="Concept that the question corresponds to",
        on_delete=models.CASCADE,
    )
    difficulty = models.FloatField(
        help_text="Question difficulty for the concept. Initially set by an expert, but will subsequently be inferred"
        " from data. A relative scale, with 0 the lowest possible and as many difficulty levels as is deemed"
        " makes sense by the expert.",
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
    last_updated = models.DateTimeField(auto_now=True)

    # map = models.ForeignKey(
    #     KnowledgeMapModel,
    #     on_delete=models.SET_NULL,
    #     help_text="The map the concept is tagged to",
    # )
    # session_id = models.TextField(
    #     null=True, blank=True, help_text="session_id of the session the question was written in"
    # )
    # author_user_id = models.ForeignKey(User, help_text="User who wrote this question", null=True, blank=True)
    # timestamp = models.DateTimeField(
    #     auto_now_add=True, help_text="Time that the question was written"
    # )
