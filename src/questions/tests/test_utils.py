from typing import Tuple

import pytest

from questions.utils import is_number


@pytest.mark.parametrize(
    "test_data",
    [
        ("2", True),
        ("27", True),
        ("3.2", True),
        ("1.2", True),
        ("1.2e2", True),
        ("-1.2e2", True),
        ("-1.2e-2", True),
        ("3^{2}", False),
        ("-1.2e-2.5", False),  # Interestingly, python only accepts ints after e
        ("5 2", False),
        ('"string', False),
        ("another string", False),
        ("[1, 2, 3, 4]", False),
        ("[1, 2, 3]", False),
        ("-1, 2, 3", False),
    ],
)
def test_is_number(test_data: Tuple[str, str]) -> None:
    assert is_number(test_data[0]) == test_data[1]
