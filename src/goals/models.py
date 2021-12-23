from django.db import models

from knowledge_maps.models import KnowledgeMapModel


class GoalModel(models.Model):
    map = models.ForeignKey(
        KnowledgeMapModel,
        related_name="goals_set",
        on_delete=models.CASCADE,
        help_text="Map this goal corresponds to",
    )
    user_id = models.TextField()
    session_id = models.TextField(
        blank=True, help_text="session_key of the session the goal was set in"
    )
    goal_concepts = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
