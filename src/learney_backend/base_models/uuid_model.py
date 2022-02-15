from uuid import uuid4

from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, help_text="Unique id")

    class Meta:
        abstract = True
