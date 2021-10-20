import json

from django.test import TestCase

from button_presses.models import ALL_BUTTONS, ButtonPressModel


class ButtonPressViewTests(TestCase):
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_SESSION_ID = "qrg8eas3afqekibzpvcev5hnvnc0dqrm"
    TEST_PAGE_EXTENSION = "/maps/edit"
    TEST_BUTTON_NAME = "open-intro"

    def check_invalid_button_name_invalid(self, invalid_button_name: str):
        response = self.client.post(
            "/api/v0/button_press",
            content_type="application/json",
            data={
                "user_id": self.TEST_USER_ID,
                "page_extension": self.TEST_PAGE_EXTENSION,
                "button_name": invalid_button_name,
                "session_id": self.TEST_SESSION_ID,
            },
        )
        assert response.status_code == 400

    def test_post_invalid_button_name_1(self):
        self.check_invalid_button_name_invalid("")

    def test_post_invalid_button_name_2(self):
        self.check_invalid_button_name_invalid("asegrliukb")

    def test_post_invalid_button_name_3(self):
        self.check_invalid_button_name_invalid("button")

    # def test_post_invalid_no_button(self):
    #     response = self.client.post(
    #         "/api/v0/goals", data={"user_id": self.TEST_USER_ID, "map_uuid": self.TEST_MAP_UUID}
    #     )
    #     assert response.status_code == 400
    #
    # def test_post_invalid_no_map_uuid(self):
    #     response = self.client.post(
    #         "/api/v0/goals", data={"user_id": self.TEST_USER_ID, "goal_concepts": self.TEST_GOALS}
    #     )
    #     assert response.status_code == 400

    def test_post_valid_all_buttons(self):
        for (valid_button_name, _) in ALL_BUTTONS:
            response = self.client.post(
                "/api/v0/button_press",
                content_type="application/json",
                data={
                    "user_id": self.TEST_USER_ID,
                    "page_extension": self.TEST_PAGE_EXTENSION,
                    "button_name": valid_button_name,
                    "session_id": self.TEST_SESSION_ID,
                },
            )
            print(f"Response received: {response.content}")
            assert response.status_code == 201
            response_dict = json.loads(response.content.decode("utf-8"))
            print(response_dict)
            assert response_dict["user_id"] == self.TEST_USER_ID
            assert response_dict["session_id"] == self.TEST_SESSION_ID
            assert response_dict["page_extension"] == self.TEST_PAGE_EXTENSION
            assert response_dict["button_name"] == valid_button_name
            assert "timestamp" in response_dict
            assert ButtonPressModel.objects.get(
                user_id=self.TEST_USER_ID,
                button_name=valid_button_name,
            )
