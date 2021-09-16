from typing import Dict


def validate_map_json(map_json: Dict) -> None:
    assert len(map_json) > 0, "map json is empty!"

    ids = [element["data"]["id"] for element in map_json["nodes"]]

    for edge in map_json["edges"]:
        assert isinstance(edge["data"]["source"], str)
        assert isinstance(edge["data"]["target"], str)
        assert edge["data"]["source"].isnumeric()
        assert edge["data"]["target"].isnumeric()
        assert edge["data"]["source"] in ids
        assert edge["data"]["target"] in ids
