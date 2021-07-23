from datetime import time

import pytest
from django.test import TestCase

from goals.models import GoalModel


class SlackBotUserModelTests(TestCase):
    TEST_USER_ID = "henrypulver@hotmail.co.uk"
    TEST_GOALS = {"1": True, "77": True}

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = GoalModel.objects.create(
            user_id=self.TEST_USER_ID,
            goal_concepts=self.TEST_GOALS,
        )
        assert created_object

    def test_get_from_db(self):
        user = GoalModel.objects.get(user_id=self.TEST_USER_ID)
        assert user.user_id == self.TEST_USER_ID
        assert user.goal_concepts == self.TEST_GOALS
        assert user.last_updated
