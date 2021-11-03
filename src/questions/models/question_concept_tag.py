from uuid import uuid4

from django.db import models


class QuestionConceptTagModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid4, help_text="Unique id for concept tag on question"
    )
    question_id = models.UUIDField(help_text="id of the question this was a response to")
    map_uuid = models.UUIDField(help_text="UUID of the map the concept is tagged to")
    concept_id = models.CharField(
        max_length=16, help_text="Concept id that the question is tagged with"
    )
