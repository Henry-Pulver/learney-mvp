from django.db import models


class QuestionLastAskedModel(models.Model):
    user_email = models.CharField(max_length=128)
    time_asked = models.DateTimeField(auto_now=True)
