import json
from uuid import UUID

import pytest
from django.test import TestCase

from learned.models import LearnedModel


class LearnedViewTests(TestCase):
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_LEARNED = {"1": True, "77": True, "32": False}
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = LearnedModel.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            user_id=self.TEST_USER_ID,
            learned_concepts=self.TEST_LEARNED,
        )
        assert created_object

    def test_get_doesnt_exist_invalid_id(self):
        response = self.client.get(
            "/api/v0/learned",
            data={"user_id": f"89{self.TEST_USER_ID}", "map_uuid": self.TEST_MAP_UUID},
        )
        assert response.status_code == 204

    def test_get_doesnt_exist_no_user_id(self):
        response = self.client.get("/api/v0/goals", data={"map_uuid": self.TEST_MAP_UUID})
        assert response.status_code == 400

    def test_get_doesnt_exist_no_map_uuid(self):
        response = self.client.get(
            "/api/v0/learned",
            data={"user_id": self.TEST_USER_ID, "learned_concepts": self.TEST_LEARNED},
        )
        assert response.status_code == 400

    def test_get_exists(self):
        response = self.client.get(
            "/api/v0/learned", data={"user_id": self.TEST_USER_ID, "map_uuid": self.TEST_MAP_UUID}
        )

        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf-8"))
        assert "id" in response_dict
        assert response_dict["user_id"] == self.TEST_USER_ID
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["learned_concepts"] == self.TEST_LEARNED
        assert "last_updated" in response_dict

    def test_post_invalid_no_user_id(self):
        response = self.client.post(
            "/api/v0/goals",
            data={
                "learned_concepts": self.TEST_LEARNED,
                "map_uuid": self.TEST_MAP_UUID,
            },
        )
        assert response.status_code == 400

    def test_post_invalid_no_map_uuid(self):
        response = self.client.post(
            "/api/v0/goals",
            data={
                "user_id": self.TEST_USER_ID,
                "learned_concepts": self.TEST_LEARNED,
            },
        )
        assert response.status_code == 400

    def test_post_invalid_no_learned_concepts(self):
        response = self.client.post(
            "/api/v0/learned",
            data={
                "user_id": self.TEST_USER_ID,
                "map_uuid": self.TEST_MAP_UUID,
            },
        )
        assert response.status_code == 400

    def test_post_valid(self):
        new_user_id = f"22{self.TEST_USER_ID}"
        response = self.client.post(
            "/api/v0/learned",
            content_type="application/json",
            data={
                "user_id": new_user_id,
                "learned_concepts": self.TEST_LEARNED,
                "map_uuid": self.TEST_MAP_UUID,
            },
        )

        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf-8"))
        print("Response received!")
        print(response_dict)
        assert "id" in response_dict
        assert response_dict["user_id"] == new_user_id
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        # assert response_dict["learned_concepts"] == self.TEST_LEARNED
        assert "last_updated" in response_dict
        assert (
            LearnedModel.objects.get(
                user_id=new_user_id, map_uuid=self.TEST_MAP_UUID
            ).learned_concepts
            == self.TEST_LEARNED
        )
