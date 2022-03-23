from typing import Dict

from django.db import models

from learney_backend.base_models import UUIDModel


class ContentTag(UUIDModel):
    name = models.CharField(max_length=64, unique=True)
    colour = models.URLField(blank=True, null=True, help_text="Thumbnail image of the author")

    last_updated = models.DateTimeField(auto_now=True)

    def json(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "colour": self.colour,
        }
