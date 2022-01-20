from django.db import models

from accounts.models import User
from knowledge_maps.models import Concept
from learney_backend.models import UUIDModel


class InferredKnowledgeState(UUIDModel):
    user = models.ForeignKey(
        User, help_text="User who this knowledge state refers to", on_delete=models.CASCADE
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        related_name="user_knowledge_states",
        help_text="The concept that this knowledge state refers to",
    )
    last_updated = models.DateTimeField(
        auto_now=True, help_text="Time that the knowledge state was last updated"
    )
