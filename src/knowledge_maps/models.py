import uuid

from django.db import models


class KnowledgeMapModel(models.Model):
    unique_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, help_text="Unique identifier for each knowledge map"
    )
    title = models.CharField(
        max_length=32, blank=True, help_text="Title of the knowledge map shown in top left corner"
    )
    description = models.TextField(
        max_length=1024,
        blank=True,
        help_text="Description of the knowledge map shown in top left corner",
    )
    version = models.IntegerField(help_text="Version number of the map", default=0)

    author_user_id = models.TextField(help_text="User ID of user who created this map")
    url_extension = models.TextField(unique=True, help_text="URL extension of the map")

    s3_bucket_name = models.TextField(
        help_text="Name of the S3 bucket that the knowledge map json is stored in"
    )
    s3_key = models.TextField(help_text="Key of the knowledge map json in S3")
    allow_suggestions = models.BooleanField(
        help_text="Whether to allow suggestions on this map", default=True
    )

    last_updated = models.DateTimeField(auto_now=True)
