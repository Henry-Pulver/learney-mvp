from django.db import models

from knowledge_maps.models import Concept
from learney_backend.models import ContentLinkPreview


class User(models.Model):
    id = models.CharField(primary_key=True, max_length=255)

    name = models.CharField(max_length=255)
    nickname = models.CharField(blank=True, max_length=255)
    given_name = models.CharField(blank=True, max_length=255)
    family_name = models.CharField(blank=True, max_length=255)

    picture = models.URLField(max_length=1000)
    locale = models.CharField(blank=True, max_length=8)

    checked_content_links = models.ManyToManyField(
        ContentLinkPreview,
        related_name="checked_by",
        help_text="The content links that this user has checked",
    )
    next_questions_concept = models.ForeignKey(
        Concept,
        on_delete=models.CASCADE,
        related_name="next_step_users",
        help_text="The concept next step for this user",
    )
