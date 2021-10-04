from uuid import uuid4

from django.db import models

from learney_web.validators import validate_numeric


class LinkClickModel(models.Model):
    id = models.UUIDField(
        primary_key=True, editable=False, help_text="Unique ID for this link click", default=uuid4
    )
    map_uuid = models.UUIDField(help_text="UUID of the map this link click corresponds to")
    user_id = models.TextField(help_text="User ID of the user who clicked the link")
    session_id = models.TextField(
        blank=True, help_text="session_key of the session the link was clicked in"
    )
    content_link_preview_id = models.IntegerField(
        help_text="Primary key of the ContentLinkPreview that was clicked",
        null=True,  # Remove once all null fields are removed from DB's!
    )
    concept_id = models.CharField(
        max_length=8,
        validators=[validate_numeric],
        help_text="ID of the concept clicked",
        null=True,  # Remove once all null fields are removed from DB's!
    )
    url = models.URLField(help_text="URL of link that was clicked")
    timestamp = models.DateTimeField(auto_now=True)
