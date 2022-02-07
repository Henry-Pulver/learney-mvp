import uuid

from django.core.cache import cache
from django.db import models
from django.db.models import Max

from learney_backend.base_models import UUIDModel


class Concept(UUIDModel):  # Currently only used in the questions trial.
    name = models.CharField(
        max_length=256, help_text="Description of the knowledge map shown in top left corner"
    )
    cytoscape_id = models.CharField(
        max_length=4, help_text="The id of the concept in the questions map cytoscape map json file"
    )
    direct_prerequisites = models.ManyToManyField(
        "self",
        related_query_name="direct_successor",
        help_text="The direct prerequisites of this concept",
    )

    @property
    def max_difficulty_level(self) -> int:
        """Gets the highest difficulty of any question on a concept.

        Tries cache first.
        """
        max_diff = cache.get(f"max_difficulty_level_{self.cytoscape_id}")
        if max_diff is None:
            max_diff = (
                self.question_templates.all().aggregate(Max("difficulty"))["difficulty__max"]
                if self.question_templates.all().exists()
                else 0
            )
            cache.set(f"max_difficulty_level_{self.cytoscape_id}", max_diff, 60 * 60 * 24)
        return max_diff

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.title or self.url_extension
