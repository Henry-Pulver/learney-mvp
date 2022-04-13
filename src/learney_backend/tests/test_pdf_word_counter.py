import datetime
import json
from pathlib import Path
from typing import Dict
from uuid import UUID

import pytest
from django.test import TestCase
from mock import patch
from rest_framework import status
from rest_framework.response import Response

from learney_backend.read_time import (
    WORDS_PER_MIN,
    count_words_in_line,
    get_pdf_info,
    get_read_time,
)


@pytest.mark.parametrize(
    "word_string, word_count",
    [
        ("Word?", 1),
        (
            "Words have  meaning only in context. Are we accounting for this ? I don't think so! !!",
            15,
        ),
    ],
)
def test_count_words_in_line(word_string: str, word_count: int):
    assert count_words_in_line(word_string) == word_count


@pytest.mark.parametrize("num_words", [1, 324, 1000, 2999, 5000, 100000])
def test_get_read_time_repeat_strings(num_words: int):
    assert get_read_time("word " * num_words) == datetime.timedelta(
        minutes=num_words / WORDS_PER_MIN
    )


@pytest.mark.parametrize(
    "word_string, word_count",
    [
        ("Word?", 1),
        (
            "Words have  meaning only in context. Are we accounting for this ? I don't think so! !!",
            15,
        ),
        ("To be \nOr\n Not to   \tbe\n????\nthat is the question.", 10),
    ],
)
def test_get_read_time_set_strings(word_string: str, word_count: int):
    assert get_read_time(word_string) == datetime.timedelta(minutes=word_count / WORDS_PER_MIN)


@pytest.mark.parametrize(
    "pdf_file_path, expected_info",
    [
        (Path("learney_backend/tests/test_files/ila0403.pdf"), {}),
        (
            Path("learney_backend/tests/test_files/Lecture33_with_Examples.pdf"),
            {
                "author_name": "",
                "description": "218\n\nChapter 4. Orthogonality\n\n4.3 Least Squares Approximations\n"
                "It often happens that Ax D b has no solution. The usual "
                "reason is: too many equations.\n"
                "The matrix has more rows than columns. There are more "
                "equations than unknowns\n"
                "(m is greater than n). The n columns span a small part of "
                "m-dimensional space. Unless all\n"
                "measurements are perfect, b is outside that column space. "
                "Elimination reaches an\n"
                "impossible equation and stops. But we can’t stop just because "
                "measurements include noise.\n"
                "To repeat: We cannot a",
                "read_time": datetime.timedelta(seconds=1687, microseconds=800000),
                "title": "D:/Editors/Kishor/LaTeX/Linear Algebra/ila4/ila4new.dvi",
            },
        ),
    ],
)
def test_get_pdf_info(pdf_file_path: Path, expected_info: Dict):
    with pdf_file_path.open("rb") as f:
        assert get_pdf_info(f) == expected_info  # type: ignore
