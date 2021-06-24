from copy import copy
from datetime import date, time

import pytest
from django.test import TestCase

from question_bot.models import AnswerModel, SlackBotUserModel


class SlackBotUserModelTests(TestCase):
    TEST_USER_ID = "henrypulver@hotmail.co.uk"
    TEST_TIMEZONE = "GMT + 4"
    RELATIVE_QUESTION_TIME = time(8, 0)
    TEST_UTC_TIME = time(hour=12, minute=30)

    def test_failed_set_up__time_wrong(self):
        with pytest.raises(Exception):
            SlackBotUserModel.objects.create(
                user_id=self.TEST_USER_ID,
                timezone=self.TEST_TIMEZONE,
                utc_time_to_send="27:77",
                relative_question_time=self.RELATIVE_QUESTION_TIME,
                on_slack=False,
                on_learney=True,
            )

    def test_failed_set_up__missing_time_to_send(self):
        with pytest.raises(Exception) as e:
            SlackBotUserModel.objects.create(
                user_id=self.TEST_USER_ID,
                timezone=self.TEST_TIMEZONE,
                relative_question_time=self.RELATIVE_QUESTION_TIME,
                on_slack=True,
                on_learney=True,
            )

    def test_failed_set_up__missing_on_slack(self):
        with pytest.raises(Exception) as e:
            SlackBotUserModel.objects.create(
                user_id=self.TEST_USER_ID,
                timezone=self.TEST_TIMEZONE,
                relative_question_time=self.RELATIVE_QUESTION_TIME,
                utc_time_to_send=self.TEST_UTC_TIME,
                on_learney=True,
            )

    def test_failed_set_up__missing_timezone(self):
        with pytest.raises(Exception) as e:
            SlackBotUserModel.objects.create(
                user_id=self.TEST_USER_ID,
                relative_question_time=self.RELATIVE_QUESTION_TIME,
                utc_time_to_send=self.TEST_UTC_TIME,
                on_learney=True,
                on_slack=False,
            )

    def test_failed_set_up__missing_relative_question_time(self):
        with pytest.raises(Exception) as e:
            SlackBotUserModel.objects.create(
                user_id=self.TEST_USER_ID,
                timezone=self.TEST_TIMEZONE,
                utc_time_to_send=self.TEST_UTC_TIME,
                on_learney=True,
                on_slack=False,
            )

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = SlackBotUserModel.objects.create(
            user_id=self.TEST_USER_ID,
            timezone=self.TEST_TIMEZONE,
            relative_question_time=self.RELATIVE_QUESTION_TIME,
            utc_time_to_send=self.TEST_UTC_TIME,
            on_slack=False,
            on_learney=True,
        )
        assert created_object

    def test_get_from_db(self):
        user = SlackBotUserModel.objects.get(user_id=self.TEST_USER_ID)
        assert user.user_id == self.TEST_USER_ID
        assert user.relative_question_time == self.RELATIVE_QUESTION_TIME
        assert user.timezone == self.TEST_TIMEZONE
        assert user.utc_time_to_send == self.TEST_UTC_TIME
        assert not user.on_slack
        assert user.slack_user_id == ""
        assert user.on_learney
        assert user.active
        assert user.active_since == date.today()
        assert user.signup_date == date.today()
        assert user.paid is False

    def test_update_db_entry(self):
        user = SlackBotUserModel.objects.get(user_id=self.TEST_USER_ID)
        user.active = False
        user.save()

        # Check start date isn't updated
        deactivated_user = SlackBotUserModel.objects.get(user_id=self.TEST_USER_ID)
        assert deactivated_user.active is False


class AnswerModelTests(TestCase):
    TEST_USER_ID = "henrypulver@hotmail.co.uk"
    TEST_Q_ID = "10_1a"
    TEST_ANSWER_GIVEN = "This is an answer... A what?"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = AnswerModel.objects.create(
            user_id=self.TEST_USER_ID,
            question_id=self.TEST_Q_ID,
            time_asked="1624463906.000300",
            time_answered=None,
        )
        assert created_object

    def test_get_from_db(self):
        question_answer = AnswerModel.objects.get(user_id="henrypulver@hotmail.co.uk")
        assert question_answer.user_id == self.TEST_USER_ID
        assert question_answer.question_id == self.TEST_Q_ID
        assert question_answer.time_asked
        assert not question_answer.answered
        assert question_answer.answer_given == ""
        assert question_answer.correct is None

    def test_update_db_entry(self):
        question_answer = AnswerModel.objects.get(user_id="henrypulver@hotmail.co.uk")
        orig_time_asked = copy(question_answer.time_asked)
        question_answer.answered = True
        question_answer.answer_given = self.TEST_ANSWER_GIVEN
        question_answer.correct = True
        question_answer.save()

        updated_answer = AnswerModel.objects.get(user_id="henrypulver@hotmail.co.uk")
        assert updated_answer.answered is True
        assert updated_answer.answer_given == self.TEST_ANSWER_GIVEN
        assert orig_time_asked == updated_answer.time_asked
        assert updated_answer.correct
        assert updated_answer.time_answered
