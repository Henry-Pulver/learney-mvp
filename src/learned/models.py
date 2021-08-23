from django.db import models


class LearnedModel(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this set of learned items corresponds to"
    )
    user_id = models.TextField()
    learned_concepts = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
