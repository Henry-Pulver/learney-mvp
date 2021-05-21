from django.db import models


class ContentLinkPreview(models.Model):
    concept = models.TextField()
    url = models.URLField(unique=True)

    title = models.TextField()
    description = models.TextField()
    image_url = models.URLField()

    preview_last_retrieved = models.DateTimeField(auto_now=True)


class ContentVote(models.Model):
    concept = models.TextField()
    url = models.URLField()

    vote = models.BooleanField()

    vote_time = models.DateTimeField(auto_now=True)
