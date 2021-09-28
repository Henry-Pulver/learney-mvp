from django.db import models


class LinkClickModel(models.Model):
    map_uuid = models.UUIDField(
        editable=False, help_text="UUID of the map this link click corresponds to"
    )
    user_id = models.TextField()
    session_id = models.TextField(
        blank=True, editable=False, help_text="session_key of the session the link was clicked in"
    )
    url = models.URLField()
    click_time = models.DateTimeField(auto_now=True)
