import json
from uuid import UUID

import pytest
from django.test import TestCase

from learney_backend.models import ContentLinkPreview, ContentVote


class ContentVoteViewTests(TestCase):
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")
    TEST_CONCEPT = "Matrix Multiplication"
    TEST_URL = "https://www.khanacademy.org/math/algebra-home/alg-matrices/alg-multiplying-matrices-by-matrices/v/matrix-multiplication-intro"
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_VOTE = True

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = ContentVote.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            concept=self.TEST_CONCEPT,
            url=self.TEST_URL,
            user_id=self.TEST_USER_ID,
            vote=self.TEST_VOTE,
        )
        assert created_object

    def test_get_doesnt_exist_invalid_id(self):
        response = self.client.get(
            "/api/v0/votes",
            data={"user_id": f"89{self.TEST_USER_ID}", "map_uuid": self.TEST_MAP_UUID},
        )
        assert response.status_code == 204

    def test_get_bad_request_no_user_id(self):
        response = self.client.get("/api/v0/votes", data={"map_uuid": self.TEST_MAP_UUID})
        assert response.status_code == 400

    def test_get_bad_request_no_map_uuid(self):
        response = self.client.get("/api/v0/votes", data={"user_id": self.TEST_USER_ID})
        assert response.status_code == 400

    def test_get_exists(self):
        response = self.client.get(
            "/api/v0/votes", data={"user_id": self.TEST_USER_ID, "map_uuid": self.TEST_MAP_UUID}
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf-8"))
        assert response_dict[self.TEST_URL] == self.TEST_VOTE
        assert len(response_dict) == 1

    def test_post_bad_request_no_map_uuid(self):
        response = self.client.post(
            "/api/v0/votes",
            content_type="application/json",
            data={
                "user_id": self.TEST_USER_ID,
                "concept": self.TEST_CONCEPT,
                "url": self.TEST_URL,
                "vote": self.TEST_VOTE,
            },
        )
        assert response.status_code == 400

    def test_post_bad_request_no_user_id(self):
        response = self.client.post(
            "/api/v0/votes",
            content_type="application/json",
            data={
                "map_uuid": self.TEST_MAP_UUID,
                "concept": self.TEST_CONCEPT,
                "url": self.TEST_URL,
                "vote": self.TEST_VOTE,
            },
        )
        assert response.status_code == 400

    def test_post_bad_request_no_url(self):
        response = self.client.post(
            "/api/v0/votes",
            content_type="application/json",
            data={
                "map_uuid": self.TEST_MAP_UUID,
                "user_id": self.TEST_USER_ID,
                "concept": self.TEST_CONCEPT,
                "vote": self.TEST_VOTE,
            },
        )
        assert response.status_code == 400

    def test_post_bad_request_no_vote(self):
        response = self.client.post(
            "/api/v0/votes",
            content_type="application/json",
            data={
                "map_uuid": self.TEST_MAP_UUID,
                "user_id": self.TEST_USER_ID,
                "concept": self.TEST_CONCEPT,
                "url": self.TEST_URL,
            },
        )
        assert response.status_code == 400

    def test_post_valid(self):
        new_user_id = f"22{self.TEST_USER_ID}"
        response = self.client.post(
            "/api/v0/votes",
            content_type="application/json",
            data={
                "map_uuid": self.TEST_MAP_UUID,
                "user_id": new_user_id,
                "concept": self.TEST_CONCEPT,
                "url": self.TEST_URL,
                "vote": self.TEST_VOTE,
            },
        )
        print(f"Response received: {response.content}")
        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf-8"))
        print(response_dict)
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["user_id"] == new_user_id
        assert response_dict["concept"] == self.TEST_CONCEPT
        assert response_dict["url"] == self.TEST_URL
        assert response_dict["vote"] == self.TEST_VOTE
        assert "vote_time" in response_dict
        assert (
            ContentVote.objects.get(user_id=new_user_id, map_uuid=self.TEST_MAP_UUID).vote
            == self.TEST_VOTE
        )


class ContentLinkPreviewViewTests(TestCase):
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")
    TEST_CONCEPT = "Matrix Multiplication"
    TEST_URL_1 = "https://app.learney.me"
    TEST_URL_2 = "https://www.khanacademy.org/math/algebra-home/alg-matrices/alg-multiplying-matrices-by-matrices/v/matrix-multiplication-intro"
    TEST_TITLE = "Learney | Multiply Two Matrices!"
    TEST_DESCRIPTION = "Henry describes how to multiply matrices! Honestly the most riveting piece of film to be recorded in human history."
    TEST_IMAGE_URL = "https://app.learney.me/static/images/2021/05/19/learney_background.png"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = ContentLinkPreview.objects.create(
            map_uuid=self.TEST_MAP_UUID,
            concept=self.TEST_CONCEPT,
            url=self.TEST_URL_1,
            title=self.TEST_TITLE,
            description=self.TEST_DESCRIPTION,
            image_url=self.TEST_IMAGE_URL,
        )
        assert created_object

    def test_get_fail_no_map_id(self):
        response = self.client.get(
            "/api/v0/link_previews",
            data={"concept": f"{self.TEST_CONCEPT}", "url": self.TEST_URL_1},
        )
        assert response.status_code == 400

    def test_get_fail_no_url(self):
        response = self.client.get(
            "/api/v0/link_previews",
            data={"concept": f"{self.TEST_CONCEPT}", "map_uuid": self.TEST_MAP_UUID},
        )
        assert response.status_code == 400

    def test_get_fail_no_concept(self):
        response = self.client.get(
            "/api/v0/link_previews",
            data={"url": f"{self.TEST_URL_1}", "map_uuid": self.TEST_MAP_UUID},
        )
        assert response.status_code == 400

    def test_get_success(self):
        response = self.client.get(
            "/api/v0/link_previews",
            data={
                "concept": f"{self.TEST_CONCEPT}",
                "map_uuid": self.TEST_MAP_UUID,
                "url": self.TEST_URL_1,
            },
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf-8"))
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["concept"] == self.TEST_CONCEPT
        assert response_dict["url"] == self.TEST_URL_1
        assert response_dict["description"] == self.TEST_DESCRIPTION
        assert response_dict["title"] == self.TEST_TITLE
        assert response_dict["image_url"] == self.TEST_IMAGE_URL

    def test_get_success_use_linkpreview_net(self):
        response = self.client.get(
            "/api/v0/link_previews",
            data={
                "concept": f"{self.TEST_CONCEPT}",
                "map_uuid": self.TEST_MAP_UUID,
                "url": self.TEST_URL_2,
            },
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf-8"))
        assert response_dict["map_uuid"] == str(self.TEST_MAP_UUID)
        assert response_dict["concept"] == self.TEST_CONCEPT
        assert response_dict["url"] == self.TEST_URL_2
        assert response_dict["description"]
        assert response_dict["title"]
        assert response_dict["image_url"]
        # Check added to database
        assert ContentLinkPreview.objects.get(url=self.TEST_URL_2)
