from typing import Dict

from knowledge_maps.json_validator import validate_map_json


def test_validate_map_json(map_json: Dict):
    validate_map_json(map_json)
