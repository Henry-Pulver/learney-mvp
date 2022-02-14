from typing import Any, Dict

from django.db import models

from learney_backend.models import ContentLinkPreview


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=255)

    name = models.CharField(max_length=255)
    nickname = models.CharField(null=True, blank=True, max_length=255)
    given_name = models.CharField(null=True, blank=True, max_length=255)
    family_name = models.CharField(null=True, blank=True, max_length=255)

    picture = models.URLField(max_length=1000)
    locale = models.CharField(null=True, blank=True, max_length=8)

    checked_content_links = models.ManyToManyField(
        ContentLinkPreview,
        related_name="checked_by",
        help_text="The content links that this user has checked",
        blank=True,
    )
    in_questions_trial = models.BooleanField(
        default=False, help_text="Whether or not they're involved in the question trial"
    )

    def __str__(self):
        return self.name
