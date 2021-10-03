import json
from uuid import UUID

import pytest
from django.test import TestCase

from learney_backend.models import ContentLinkPreview
from link_clicks.models import LinkClickModel


class LinkClickViewTests(TestCase):
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_SESSION_ID = "qrg8eas3afqekibzpvcev5hnvnc0dqrm"
    TEST_CONCEPT = "Matrix Multiplication"
    TEST_CONCEPT_ID = "2"
    TEST_URL = "https://www.khanacademy.org/math/algebra-home/alg-matrices/alg-multiplying-matrices-by-matrices/v/matrix-multiplication-intro"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = ContentLinkPreview.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            concept=self.TEST_CONCEPT,
            concept_id=self.TEST_CONCEPT_ID,
            url=self.TEST_URL,
            title="Matrix Mult | Khan Academy",
            description="This is a Khan Academy video about matrices",
            image_url="",
        )
        assert created_object

    def check_missing_argument_fails(self, argument_to_remove: str) -> None:
        session = self.client.session
        session["session_key"] = self.TEST_SESSION_ID
        session.save()
        data = {
            "user_id": self.TEST_USER_ID,
            "url": self.TEST_URL,
            "map_uuid": self.TEST_MAP_UUID,
            "concept_id": self.TEST_CONCEPT_ID,
        }
        data.pop(argument_to_remove)
        response = self.client.post(
            "/api/v0/link_click",
            content_type="application/json",
            data=data,
        )
        assert response.status_code == 400

    def test_post_invalid_button_name_1(self):
        self.check_missing_argument_fails("user_id")

    def test_post_invalid_button_name_2(self):
        self.check_missing_argument_fails("url")

    def test_post_invalid_button_name_3(self):
        self.check_missing_argument_fails("map_uuid")

    def test_post_invalid_button_name_4(self):
        self.check_missing_argument_fails("concept_id")

    def test_post_no_content_link_preview(self):
        session = self.client.session
        session["session_key"] = self.TEST_SESSION_ID
        session.save()
        response = self.client.post(
            "/api/v0/link_click",
            content_type="application/json",
            data={
                "user_id": self.TEST_USER_ID,
                "url": self.TEST_URL,
                "map_uuid": self.TEST_MAP_UUID,
                "concept_id": "3",
            },
        )
        assert response.status_code == 400

    def test_post_valid(self):
        session = self.client.session
        session["session_key"] = self.TEST_SESSION_ID
        session.save()
        new_user_id = f"89{self.TEST_USER_ID}"

        response = self.client.post(
            "/api/v0/link_click",
            content_type="application/json",
            data={
                "user_id": new_user_id,
                "url": self.TEST_URL,
                "map_uuid": self.TEST_MAP_UUID,
                "concept_id": self.TEST_CONCEPT_ID,
            },
        )

        print(f"Response received: {response.content}")
        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf-8"))
        print(response_dict)
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["user_id"] == new_user_id
        assert response_dict["session_id"]
        assert response_dict["content_link_preview_id"]
        assert response_dict["concept_id"] == self.TEST_CONCEPT_ID
        assert response_dict["url"] == self.TEST_URL
        assert "timestamp" in response_dict
        assert LinkClickModel.objects.filter(user_id=new_user_id).count() == 1
