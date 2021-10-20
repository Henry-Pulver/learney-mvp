from django.db import models

from learney_web.validators import validate_numeric


class ContentLinkPreview(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this content link corresponds to"
    )
    concept = models.TextField(help_text="Name of the concept the link corresponds to")
    concept_id = models.CharField(
        max_length=8,
        validators=[validate_numeric],
        help_text="ID of the concept the link corresponds to (defined in the map json)",
        null=True,  # Remove once all null fields are removed from DB's!
    )
    url = models.URLField(help_text="The URL of the link clicked")

    title = models.TextField(
        blank=True,
        help_text="Title of the link preview - shows as the title of the item of content",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the link preview - shows below the title of the content",
    )
    image_url = models.URLField(
        blank=True, null=True, help_text="Thumbnail image of the link preview"
    )

    preview_last_updated = models.DateTimeField(auto_now=True)


class ContentVote(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this content link corresponds to"
    )
    user_id = models.TextField(default="")
    session_id = models.TextField(
        blank=True,
        help_text="session_key of the session in which the vote was made",
    )
    concept = models.TextField()
    url = models.URLField()

    vote = models.BooleanField(
        null=True,
        help_text="The direction of the vote on the link - None is invalid (broken data), True is upvote and False is downvote",
    )

    timestamp = models.DateTimeField(auto_now=True)
