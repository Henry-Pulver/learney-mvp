from typing import Any, Dict, Optional, Union
from uuid import UUID

from django.core.cache import cache
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

    @staticmethod
    def cache_name(user_id: str, map_uuid: Union[str, UUID]) -> str:
        return f"learned_{user_id}_{map_uuid}"

    @staticmethod
    def get(user_id: str, map_uuid: str) -> Optional["LearnedModel"]:
        learned = cache.get(LearnedModel.cache_name(user_id, map_uuid))
        if learned is None:
            learned_queryset = LearnedModel.objects.filter(user_id=user_id, map=map_uuid)
            learned = learned_queryset.latest("timestamp") if learned_queryset.exists() else None
            cache.set(LearnedModel.cache_name(user_id, map_uuid), learned, 60 * 60 * 24)
        return learned

    def save(self, *args, **kwargs) -> None:
        super(LearnedModel, self).save(*args, **kwargs)
        cache.set(LearnedModel.cache_name(self.user_id, self.map.unique_id), self, 60 * 60 * 24)

    def json(self) -> Dict[str, Any]:
        return {
            "pk": self.pk,
            "map": self.map.unique_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "learned_concepts": self.learned_concepts,
            "timestamp": self.timestamp,
        }
