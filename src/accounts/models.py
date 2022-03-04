import math
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple

from django.db import models

from learney_backend.models import ContentLinkPreview
from learney_backend.views import UTC


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
    utc_tz_difference = models.FloatField(
        default=0,
        help_text="The user's timezone relative to UTC in hours. E.g. 4 = UTC+4 and -5 = UTC-5",
    )
    questions_streak = models.IntegerField(
        default=0, help_text="How many days in a row they've completed a question batch"
    )

    def __str__(self):
        return self.name

    def tz_adjusted_last_batch_finished_time(self) -> Optional[datetime]:
        """Returns the last time this user completed a question batch, adjusted for their
        timezone."""
        # Below is actually the completed batch that was started most recently.
        completed_batches = self.question_batches.exclude(completed="")
        if completed_batches.count() == 0:
            return None
        last_completed_batch = completed_batches.latest("time_started")
        time_finished = (
            last_completed_batch.time_started + last_completed_batch.time_taken_to_complete
        )

        return self.adjusted_to_tz(time_finished)

    def tz_hours_mins(self) -> Tuple[int, int]:
        tz_hours = (
            math.floor(self.utc_tz_difference)
            if self.utc_tz_difference >= 0
            else math.ceil(self.utc_tz_difference)
        )
        tz_mins = 60 * self.utc_tz_difference - tz_hours
        return tz_hours, tz_mins

    def adjusted_to_tz(self, datetime_to_adjust: datetime) -> datetime:
        tz_hours, tz_mins = self.tz_hours_mins()
        return datetime_to_adjust + timedelta(hours=tz_hours, minutes=tz_mins)

    def tz_adjusted_today(self) -> date:
        return self.adjusted_to_tz(UTC.localize(datetime.utcnow())).date()

    def question_batch_finished_yesterday(self) -> bool:
        """Did this user complete a question batch yesterday?"""
        # Get user time difference
        tz_hours, tz_mins = self.tz_hours_mins()
        time_diff = time(hour=tz_hours, minute=tz_mins)
        # Get their timezone's start of yesterday and today in UTC
        yesterday_start = datetime.combine(self.tz_adjusted_today() - timedelta(days=1), time_diff)
        today_start = datetime.combine(self.tz_adjusted_today(), time_diff)
        # Check if a question batch was completed yesterday by one of them!
        return (
            self.question_batches.exclude(completed="")
            .filter(time_started__gte=yesterday_start, time_started__lte=today_start)
            .exists()
        )

    def question_batch_finished_today(self) -> bool:
        """Did this user complete a question batch today?"""
        last_batch_finish_time = self.tz_adjusted_last_batch_finished_time()
        return (
            last_batch_finish_time.date() == self.tz_adjusted_today()
            if last_batch_finish_time
            else False
        )
