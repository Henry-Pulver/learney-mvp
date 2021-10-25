from django.db import models


class GoalModel(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this goal corresponds to"
    )
    user_id = models.TextField()
    session_id = models.TextField(
        blank=True, help_text="session_key of the session the goal was set in"
    )
    goal_concepts = models.JSONField()
    timestamp = models.DateTimeField(auto_now=True)
