import json
from uuid import UUID, uuid4

import pytest
from django.test import TestCase

from knowledge_maps.json_validator import validate_map_json
from knowledge_maps.models import KnowledgeMapModel
from knowledge_maps.tests.conftest import TEST_FILE_PATHS, get_map_json


class KnowledgeMapViewTests(TestCase):
    TEST_USER_ID = "henrypulver13@gmail.com"
    TEST_MAP_UUID = UUID("015a52d3-1e58-47d6-abf4-35a60c0928ab")
    TEST_URL_EXT = "original_map"
    TEST_S3_BUCKET = "learney-prod"
    TEST_S3_KEY = "TEST_positions_map_v013.json"
    TEST_ALTERNATIVE_S3_KEY = "TEST_alternative.json"

    @pytest.fixture(scope="class", autouse=True)
    def set_up(self):
        created_object = KnowledgeMapModel.objects.create(
            unique_id=self.TEST_MAP_UUID,
            author_user_id=self.TEST_USER_ID,
            url_extension=self.TEST_URL_EXT,
            s3_bucket_name=self.TEST_S3_BUCKET,
            s3_key=self.TEST_S3_KEY,
        )
        self.version = created_object.version
        self.map_jsons = [get_map_json(map_json_path) for map_json_path in TEST_FILE_PATHS]
        assert created_object

    def test_get_error_no_map_id(self):
        response = self.client.get("/api/v0/knowledge_maps", data={"version": self.version})
        assert response.status_code == 400

    def test_get_error_no_version(self):
        response = self.client.get("/api/v0/knowledge_maps", data={"map_uuid": self.TEST_MAP_UUID})
        assert response.status_code == 400

    def test_get_doesnt_exist(self):
        response = self.client.get(
            "/api/v0/knowledge_maps", data={"map_uuid": uuid4(), "version": self.version}
        )
        assert response.status_code == 204

    def test_get_exists(self):
        response = self.client.get(
            "/api/v0/knowledge_maps", data={"map_uuid": self.TEST_MAP_UUID, "version": self.version}
        )
        assert response.status_code == 200
        map_json = json.loads(json.loads(response.content.decode("utf-8")))
        validate_map_json(map_json)

    def test_put_invalid_no_map_data(self):
        response = self.client.put(
            "/api/v0/knowledge_maps",
            content_type="application/json",
            data={
                "map_uuid": self.TEST_MAP_UUID,
            },
        )
        assert response.status_code == 400

    def test_put_invalid_no_map_uuid(self):
        for map_json in self.map_jsons:
            response = self.client.put(
                "/api/v0/knowledge_maps",
                content_type="application/json",
                data={
                    "map_data": map_json,
                },
            )
            assert response.status_code == 400

    def test_put_invalid_no_entry_exists(self):
        for map_json in self.map_jsons:
            response = self.client.put(
                "/api/v0/knowledge_maps",
                content_type="application/json",
                data={
                    "map_uuid": uuid4(),
                    "map_data": map_json,
                },
            )
            assert response.status_code == 204

    def test_put_valid(self):
        for map_json in self.map_jsons:
            response = self.client.put(
                "/api/v0/knowledge_maps",
                content_type="application/json",
                data={
                    "map_uuid": self.TEST_MAP_UUID,
                    "map_data": map_json,
                },
            )
            assert response.status_code == 201
            response_dict = json.loads(response.content.decode("utf-8"))
            assert response_dict["unique_id"] == str(self.TEST_MAP_UUID)
            assert response_dict["version"] == self.version + 1
            assert response_dict["author_user_id"] == self.TEST_USER_ID
            assert response_dict["url_extension"] == self.TEST_URL_EXT
            assert response_dict["s3_bucket_name"] == self.TEST_S3_BUCKET
            assert response_dict["s3_key"] == self.TEST_S3_KEY
            assert "last_updated" in response_dict
            map_entry = KnowledgeMapModel.objects.get(
                unique_id=self.TEST_MAP_UUID, version=self.version + 1
            )
            assert map_entry.s3_key == self.TEST_S3_KEY
            self.version += 1

    def test_put_valid_update_s3_key(self):
        for map_json in self.map_jsons:
            response = self.client.put(
                "/api/v0/knowledge_maps",
                content_type="application/json",
                data={
                    "map_uuid": self.TEST_MAP_UUID,
                    "map_data": map_json,
                    "s3_key": self.TEST_ALTERNATIVE_S3_KEY,
                },
            )
            assert response.status_code == 201
            response_dict = json.loads(response.content.decode("utf-8"))
            assert response_dict["unique_id"] == str(self.TEST_MAP_UUID)
            assert response_dict["version"] == self.version + 1
            assert response_dict["author_user_id"] == self.TEST_USER_ID
            assert response_dict["url_extension"] == self.TEST_URL_EXT
            assert response_dict["s3_bucket_name"] == self.TEST_S3_BUCKET
            assert response_dict["s3_key"] == self.TEST_ALTERNATIVE_S3_KEY
            assert "last_updated" in response_dict
            map_entry = KnowledgeMapModel.objects.get(
                unique_id=self.TEST_MAP_UUID, version=self.version + 1
            )
            assert map_entry.s3_key == self.TEST_ALTERNATIVE_S3_KEY
            self.version += 1
