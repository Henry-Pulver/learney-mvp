from django.db import models


class SlackBotUserModel(models.Model):
    # Not an EmailField for legacy reasons
    user_email = models.CharField(primary_key=True, max_length=128)

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
