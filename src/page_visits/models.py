from django.db import models


class PageVisitModel(models.Model):
    user_id = models.TextField()
    session_id = models.TextField(
        blank=True, editable=False, help_text="session_key of the session"
    )
    page_extension = models.TextField(default="", help_text="URL extension of the page visited")
    timestamp = models.DateTimeField(auto_now=True)
