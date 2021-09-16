import json
from pathlib import Path
from typing import Dict

import pytest

TEST_FILE_DIR = Path(__file__).parent / "test_files"
TEST_FILE_PATHS = [test_file for test_file in TEST_FILE_DIR.iterdir()]


@pytest.fixture(scope="class", params=TEST_FILE_PATHS)
def map_json(request) -> Dict:
    return get_map_json(request.param)


def get_map_json(map_json_path: Path) -> Dict:
    with map_json_path.open("r") as json_file:
        return json.load(json_file)
