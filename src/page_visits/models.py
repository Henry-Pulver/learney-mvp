from django.db import models


class PageVisitModel(models.Model):
    user_id = models.TextField()
    visit_time = models.DateTimeField(auto_now=True)
