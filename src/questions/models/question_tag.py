from uuid import uuid4

from django.db import models

from knowledge_maps.models import KnowledgeMapModel
from learney_web.validators import validate_numeric
from questions.models import QuestionModel


class QuestionTagModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid4, help_text="Unique id for tag on question"
    )
    question = models.ForeignKey(
        QuestionModel,
        on_delete=models.PROTECT,
        related_name="tags",
        help_text="the question this is a tag of",
    )
    map = models.ForeignKey(
        KnowledgeMapModel,
        on_delete=models.SET_NULL,
        null=True,
        help_text="the map the concept is tagged to",
    )
    concept_id = models.CharField(
        max_length=16,
        help_text="Concept id that the question is tagged with",
        validators=[validate_numeric],
    )
