import uuid
from pathlib import Path
from typing import Optional, Union

from django.core.cache import cache
from django.db import models
from django.db.models import Max

from learney_backend.base_models import UUIDModel
from learney_web.settings import AWS_CREDENTIALS
from learney_web.utils import S3_CACHE_DIR, retrieve_map_from_s3


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
        symmetrical=False,
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

    def get_cache_file_location(self) -> Path:
        s3_key_filename = Path(self.s3_key)
        filename = f"{s3_key_filename.stem}_{self.version}{s3_key_filename.suffix}"
        return S3_CACHE_DIR / self.s3_bucket_name / filename

    def retrieve_map(self) -> bytes:
        """Check local file first, then get it from S3 if tricky."""
        cache_file_location = self.get_cache_file_location()

        if cache_file_location.exists():
            with cache_file_location.open("r") as cache_file:
                read_cache_file = cache_file.read()
            return bytes(read_cache_file, "utf-8")
        else:
            map_byte_str = retrieve_map_from_s3(self.s3_bucket_name, self.s3_key, AWS_CREDENTIALS)
            cache_file_location.parent.mkdir(exist_ok=True, parents=True)
            with cache_file_location.open("w") as cache_file:
                cache_file.write(map_byte_str.decode("utf-8"))
            return map_byte_str

    @staticmethod
    def cache_name(url_extension: str) -> str:
        return f"map_{url_extension}"

    @staticmethod
    def get(url_extension: str) -> Optional["KnowledgeMapModel"]:
        map_entry = cache.get(KnowledgeMapModel.cache_name(url_extension))
        if map_entry is None:
            map_queryset = KnowledgeMapModel.objects.filter(url_extension=url_extension)
            map_entry = map_queryset.first() if map_queryset.exists() else None
            cache.set(KnowledgeMapModel.cache_name(url_extension), map_entry, 60 * 60 * 24)
        return map_entry

    def save(self, *args, **kwargs) -> None:
        super(KnowledgeMapModel, self).save(*args, **kwargs)
        cache.set(KnowledgeMapModel.cache_name(self.url_extension), self, 60 * 60 * 24)
