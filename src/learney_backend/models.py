from django.db import models


class ContentLinkPreview(models.Model):
    concept = models.TextField()
    url = models.URLField(unique=True)

    title = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)

    preview_last_retrieved = models.DateTimeField(auto_now=True)


class ContentVote(models.Model):
    concept = models.TextField()
    url = models.URLField()
    user_id = models.TextField(default="")

    vote = models.BooleanField()

    vote_time = models.DateTimeField(auto_now=True)
