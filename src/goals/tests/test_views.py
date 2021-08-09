import json
from uuid import UUID

import pytest
from django.test import TestCase

from goals.models import GoalModel


class GoalViewTests(TestCase):
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_GOALS = {"1": True, "77": True}
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = GoalModel.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            user_id=self.TEST_USER_ID,
            goal_concepts=self.TEST_GOALS,
        )
        assert created_object

    def test_get_doesnt_exist_invalid_id(self):
        response = self.client.get(
            "/api/v0/goals",
            data={"user_id": f"89{self.TEST_USER_ID}", "map_uuid": self.TEST_MAP_UUID},
        )
        assert response.status_code == 204

    def test_get_doesnt_exist_no_user_id(self):
        response = self.client.get("/api/v0/goals", data={"map_uuid": self.TEST_MAP_UUID})
        assert response.status_code == 400

    def test_get_doesnt_exist_no_map_uuid(self):
        response = self.client.get("/api/v0/goals", data={"user_id": self.TEST_USER_ID})
        assert response.status_code == 400

    def test_get_exists(self):
        response = self.client.get(
            "/api/v0/goals", data={"user_id": self.TEST_USER_ID, "map_uuid": self.TEST_MAP_UUID}
        )

        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf-8"))
        assert "id" in response_dict
        assert response_dict["user_id"] == self.TEST_USER_ID
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["goal_concepts"] == self.TEST_GOALS
        assert "last_updated" in response_dict

    def test_post_invalid_id(self):
        response = self.client.post(
            "/api/v0/goals",
            data={"user_id": f"89{self.TEST_USER_ID}", "goal_concepts": self.TEST_GOALS},
        )
        assert response.status_code == 400

    def test_post_invalid_no_goals(self):
        response = self.client.post(
            "/api/v0/goals", data={"user_id": self.TEST_USER_ID, "map_uuid": self.TEST_MAP_UUID}
        )
        assert response.status_code == 400

    def test_post_invalid_no_map_uuid(self):
        response = self.client.post(
            "/api/v0/goals", data={"user_id": self.TEST_USER_ID, "goal_concepts": self.TEST_GOALS}
        )
        assert response.status_code == 400

    def test_post_valid(self):
        new_user_id = f"22{self.TEST_USER_ID}"
        response = self.client.post(
            "/api/v0/goals",
            content_type="application/json",
            data={
                "user_id": new_user_id,
                "goal_concepts": str(self.TEST_GOALS),
                "map_uuid": self.TEST_MAP_UUID,
            },
        )

        print(f"Response received: {response.content}")
        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf-8"))
        print(response_dict)
        assert "id" in response_dict
        assert response_dict["user_id"] == new_user_id
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        # assert response_dict["goal_concepts"] == self.TEST_GOALS
        assert "last_updated" in response_dict
        assert GoalModel.objects.get(
            user_id=new_user_id, map_uuid=self.TEST_MAP_UUID
        ).goal_concepts == str(self.TEST_GOALS)
