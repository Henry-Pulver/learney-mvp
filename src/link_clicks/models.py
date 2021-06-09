from django.db import models


class LinkClickModel(models.Model):
    url = models.URLField()
    user_id = models.TextField()
    click_time = models.DateTimeField(auto_now=True)
