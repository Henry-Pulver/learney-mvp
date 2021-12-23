from django.db import models

from knowledge_maps.models import KnowledgeMapModel


class LearnedModel(models.Model):
    map = models.ForeignKey(
        KnowledgeMapModel,
        related_name="learned",
        on_delete=models.CASCADE,
        help_text="Map this learned dictionary corresponds to",
    )
    user_id = models.TextField()
    session_id = models.TextField(
        blank=True,
        help_text="session_key of the session that the concept was learned in",
    )
    learned_concepts = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
