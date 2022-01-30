import json

import pytest

from learney_web.settings import AWS_CREDENTIALS
from learney_web.utils import get_prerequisite_dict, retrieve_map_from_s3


def test_get_prereq_dict_small_map():
    test_json = {
        "nodes": [
            {"data": {"id": "1"}},
            {"data": {"id": "2"}},
            {"data": {"id": "3"}},
            {"data": {"id": "4"}},
            {"data": {"id": "5"}},
        ],
        "edges": [
            {"data": {"target": "2", "source": "1"}},
            {"data": {"source": "2", "target": "3"}},
            {"data": {"source": "3", "target": "4"}},
            {"data": {"source": "3", "target": "4"}},
            {"data": {"source": "3", "target": "5"}},
        ],
    }
    expected_output = {
        "1": set(),
        "2": {"1"},
        "3": {"2", "1"},
        "4": {"2", "3", "1"},
        "5": {"2", "3", "1"},
    }
    assert get_prerequisite_dict(test_json) == expected_output


# @pytest.mark.parametrize("s3_key", ["questions_map.json"])
# def test_get_prereq_dict_full_maps(s3_key: str):
def test_get_prereq_dict_full_maps():
    s3_key = "positions_map_v013.json"
    k_map = json.loads(
        retrieve_map_from_s3(
            s3_bucket_name="learney-prod",
            s3_key=s3_key,
            aws_credentials=AWS_CREDENTIALS,
        )
    )
    assert "140" in get_prerequisite_dict(k_map)["41"]
    assert "142" in get_prerequisite_dict(k_map)["41"]
    assert "132" in get_prerequisite_dict(k_map)["75"]
    assert "148" in get_prerequisite_dict(k_map)["75"]
