# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class SlackBotUserModel(models.Model):
    # At present, this is their email address so we can see their Slack.
    # Long term it will be a unique string
    user_id = models.CharField(primary_key=True, max_length=128)

    num_questions_per_day = models.IntegerField(default=5)
    relative_question_time = models.TimeField()
    timezone = models.CharField(max_length=16)
    utc_time_to_send = models.TimeField(auto_now=False)

    on_slack = models.BooleanField()
    slack_user_id = models.CharField(max_length=64, blank=True, default="")
    on_learney = models.BooleanField()
    goal_set = models.BooleanField(default=False)

    # Use this to deactivate accounts
    active = models.BooleanField(default=True)
    active_since = models.DateField(auto_now=True, blank=True, null=True)
    signup_date = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)


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


class QuestionLastAskedModel(models.Model):
    user_id = models.CharField(max_length=128)
    time_asked = models.DateTimeField(auto_now=True)
