from typing import Dict

from django.db import models

from learney_backend.base_models import UUIDModel


class ContentTag(UUIDModel):
    name = models.CharField(max_length=64, unique=True)
    colour = models.CharField(help_text="hex colour code of the tag", max_length=7)

    last_updated = models.DateTimeField(auto_now=True)

    def json(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "colour": self.colour,
        }
