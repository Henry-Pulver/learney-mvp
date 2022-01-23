from django.db import models

from knowledge_maps.models import KnowledgeMapModel
from learney_backend.models import ContentLinkPreview


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
