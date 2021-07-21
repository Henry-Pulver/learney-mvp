from django.db import models


class AnswerModel(models.Model):
    # Add when asking a question
    user_id = models.CharField(max_length=128)
    question_id = models.CharField(max_length=16)
    question_type = models.CharField(max_length=16)
    question_text = models.TextField(max_length=1024)
    answer_type = models.CharField(max_length=16)
    correct_answer = models.TextField(default="", blank=True, max_length=256)
    feedback = models.TextField(max_length=1024)
    time_asked = models.CharField(max_length=32)

    # Change when question is answered
    answered = models.BooleanField(default=False)
    answer_given = models.TextField(default="", blank=True, max_length=256)
    correct = models.BooleanField(blank=True, null=True)
    time_answered = models.DateTimeField(auto_now=True, null=True)
