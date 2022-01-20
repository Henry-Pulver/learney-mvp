from uuid import uuid4

from django.db import models

from knowledge_maps.models import KnowledgeMapModel
from learney_web.validators import validate_numeric


class ContentLinkPreview(models.Model):
    map = models.ForeignKey(
        KnowledgeMapModel,
        on_delete=models.CASCADE,
        related_name="link_previews",
        help_text="Map this content link corresponds to",
    )
    concept = models.TextField(help_text="Name of the concept the link corresponds to")
    concept_id = models.CharField(
        max_length=8,
        validators=[validate_numeric],
        help_text="ID of the concept the link corresponds to (defined in the map json)",
        null=True,  # Remove once all null fields are removed from DB's!
    )
    url = models.URLField(max_length=2048, help_text="The resource URL")

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
    map = models.ForeignKey(
        KnowledgeMapModel,
        on_delete=models.CASCADE,
        related_name="votes",
        help_text="Map this content link corresponds to",
    )
    user_id = models.TextField(default="")
    session_id = models.TextField(
        blank=True,
        help_text="session_key of the session in which the vote was made",
    )
    content_link_preview = models.ForeignKey(
        ContentLinkPreview,
        on_delete=models.CASCADE,
        related_name="votes",
        help_text="The ContentLinkPreview that was voted on",
        null=True,
    )
    concept = models.TextField(help_text="Name of the concept the content URL corresponds to")
    url = models.URLField(help_text="Resource URL voted on")

    vote = models.BooleanField(
        null=True,
        help_text="The direction of the vote on the link - None is invalid (broken data), True is upvote and False is downvote",
    )

    timestamp = models.DateTimeField(auto_now_add=True)


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, help_text="Unique id")

    class Meta:
        abstract = True
