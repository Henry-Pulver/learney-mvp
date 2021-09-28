from django.db import models


class ContentLinkPreview(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this content link corresponds to"
    )
    concept = models.TextField()
    url = models.URLField()

    title = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, null=True)

    preview_last_updated = models.DateTimeField(auto_now=True)


class ContentVote(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this content link corresponds to"
    )
    user_id = models.TextField(default="")
    session_id = models.TextField(
        blank=True,
        editable=False,
        help_text="session_key of the session in which the vote was made",
    )
    concept = models.TextField()
    url = models.URLField()

    vote = models.BooleanField()

    vote_time = models.DateTimeField(auto_now=True)
