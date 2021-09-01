from django.db import models


class GoalModel(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this goal corresponds to"
    )
    user_id = models.TextField()
    goal_concepts = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
