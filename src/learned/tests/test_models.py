from copy import copy
from datetime import date, time
from uuid import UUID

import pytest
from django.test import TestCase

from learned.models import LearnedModel


class LearnedModelTests(TestCase):
    TEST_USER_ID = "henrypulver@hotmail.co.uk"
    TEST_LEARNED = {"1": True, "77": True}
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = LearnedModel.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            user_id=self.TEST_USER_ID,
            learned_concepts=self.TEST_LEARNED,
        )
        assert created_object

    def test_get_from_db(self):
        user = LearnedModel.objects.get(user_id=self.TEST_USER_ID)
        assert user.map_uuid == self.TEST_MAP_UUID
        assert user.user_id == self.TEST_USER_ID
        assert user.learned_concepts == self.TEST_LEARNED
        assert user.timestamp
