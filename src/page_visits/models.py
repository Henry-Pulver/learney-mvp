from django.db import models


class PageVisitModel(models.Model):
    user_id = models.TextField()
    page_extension = models.TextField(default="", help_text="URL extension of the page visited")
    visit_time = models.DateTimeField(auto_now=True)
