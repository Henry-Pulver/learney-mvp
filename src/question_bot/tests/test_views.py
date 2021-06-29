import random
from datetime import date, datetime, time, timedelta

from django.test import TestCase
from mock import Mock, patch

from question_bot.models import SlackBotUserModel
from question_bot.slack_message_text import Messages
from question_bot.utils import get_nearest_half_hour


class QuestionBotViewTests(TestCase):
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_TIMEZONE = "GMT + 4"
    RELATIVE_QUESTION_TIME = time(8, 0)
    TEST_UTC_TIME = time(hour=12, minute=30)

    def test_send_questions(self):
        SlackBotUserModel.objects.create(
            user_id=self.TEST_USER_ID,
            timezone=self.TEST_TIMEZONE,
            relative_question_time=self.RELATIVE_QUESTION_TIME,
            utc_time_to_send=get_nearest_half_hour(datetime.utcnow().time()),
            on_slack=True,
            on_learney=True,
            active=True,
        )
        with patch("question_bot.views.send_questions") as mock_question_send:
            response = self.client.get("/api/v0/questions")
            assert response.content.decode("utf-8") == '"Questions sent to 1 users"'
            mock_question_send.assert_called()

    def test_remind_about_activation(self):
        SlackBotUserModel.objects.create(
            user_id=self.TEST_USER_ID,
            timezone=self.TEST_TIMEZONE,
            relative_question_time=self.RELATIVE_QUESTION_TIME,
            utc_time_to_send=get_nearest_half_hour(datetime.utcnow().time()),
            on_slack=True,
            on_learney=True,
            goal_set=False,
            active=False,
        )
        today = date.today()
        random.seed(1)
        with patch("question_bot.views.WebClient.chat_postMessage") as mock_slack_client:
            with patch(
                "question_bot.views.date", Mock(today=Mock(return_value=today + timedelta(days=3)))
            ):
                response = self.client.get("/api/v0/questions")
                random.seed(1)
                mock_slack_client.assert_called_with(
                    channel=self.TEST_USER_ID, text=Messages.dont_forget_to_activate(3)
                )
                assert response.content.decode("utf-8") == '"Questions sent to 0 users"'


# TODO: Write tests for literally every view (1 day)
