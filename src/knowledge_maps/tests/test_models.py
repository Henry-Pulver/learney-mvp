from uuid import UUID, uuid4

import pytest
from django.test import TestCase

from knowledge_maps.models import KnowledgeMapModel


class SlackBotUserModelTests(TestCase):
    TEST_USER_ID = "henrypulver@hotmail.co.uk"
    TEST_UUID = uuid4()
    TEST_URL_EXTENSION1 = "test_map1"
    TEST_URL_EXTENSION2 = "test_map2"
    TEST_BUCKET = "learney-test"
    TEST_KEY1 = "positions_map_v013.json"
    TEST_KEY2 = "positions_map_v012.json"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = KnowledgeMapModel.objects.create(
            unique_id=self.TEST_UUID,
            author_user_id=self.TEST_USER_ID,
            url_extension=self.TEST_URL_EXTENSION1,
            s3_bucket_name=self.TEST_BUCKET,
            s3_key=self.TEST_KEY1,
        )
        assert created_object
        created_object_no_uuid = KnowledgeMapModel.objects.create(
            author_user_id=self.TEST_USER_ID,
            url_extension=self.TEST_URL_EXTENSION2,
            s3_bucket_name=self.TEST_BUCKET,
            s3_key=self.TEST_KEY2,
        )
        assert created_object_no_uuid

    def test_get_key_1_from_db(self):
        user = KnowledgeMapModel.objects.get(unique_id=self.TEST_UUID)
        assert user.unique_id == self.TEST_UUID
        assert user.author_user_id == self.TEST_USER_ID
        assert user.s3_bucket_name == self.TEST_BUCKET
        assert user.s3_key == self.TEST_KEY1
        assert user.last_updated

    def test_get_key_2_from_db(self):
        user = KnowledgeMapModel.objects.get(s3_key=self.TEST_KEY2)
        assert isinstance(user.unique_id, UUID)
