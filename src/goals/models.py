from django.db import models


class GoalModel(models.Model):
    # id = models.IntegerField(primary_key=True)
    user_id = models.TextField()
    goal_concepts = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
