from django.db import models


class LearnedModel(models.Model):
    user_id = models.TextField()
    learned_concepts = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
