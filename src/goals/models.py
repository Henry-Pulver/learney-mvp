from typing import Any, Dict, Optional, Union
from uuid import UUID

from django.core.cache import cache
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

    @staticmethod
    def cache_name(user_id: str, map_uuid: Union[str, UUID]) -> str:
        return f"goal_{user_id}_{map_uuid}"

    @staticmethod
    def get(user_id: str, map_uuid: str) -> Optional["GoalModel"]:
        goals = cache.get(GoalModel.cache_name(user_id, map_uuid))
        if goals is None:
            goals_queryset = GoalModel.objects.filter(user_id=user_id, map=map_uuid)
            goals = goals_queryset.latest("timestamp") if goals_queryset.exists() else None
            cache.set(GoalModel.cache_name(user_id, map_uuid), goals, 60 * 60 * 24)
        return goals

    def save(self, *args, **kwargs) -> None:
        super(GoalModel, self).save(*args, **kwargs)
        cache.set(GoalModel.cache_name(self.user_id, self.map.unique_id), self, 60 * 60 * 24)

    def json(self) -> Dict[str, Any]:
        return {
            "pk": self.pk,
            "map": self.map.unique_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "goal_concepts": self.goal_concepts,
            "timestamp": self.timestamp,
        }
