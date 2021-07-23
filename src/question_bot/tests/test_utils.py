import unittest
from datetime import time
from typing import Dict, Set

import pytest
from django.test import TestCase

from question_bot.utils import MapStatus, check_answer, get_nearest_half_hour, get_utc_time_to_send


@pytest.mark.parametrize(
    "t,expected_output",
    [
        (time(1, 46), time(2, 0)),
        (time(17, 23), time(17, 30)),
        (time(9, 30), time(9, 30)),
        (time(23, 0), time(23, 0)),
        (time(23, 46), time(0, 0)),
    ],
)
def test_get_nearest_half_hour(t: time, expected_output: time):
    assert get_nearest_half_hour(t) == expected_output


@pytest.mark.parametrize(
    "time_str,time_difference,expected_output",
    [
        ("15:30", "GMT + 4", time(11, 30)),
        ("7:30", "GMT + 8", time(23, 30)),
        ("19:00", "GMT - 6", time(1, 0)),
    ],
)
def test_get_utc_time_to_send(time_str: str, time_difference: str, expected_output: time):
    assert get_utc_time_to_send(time_str, time_difference) == expected_output


@pytest.mark.parametrize(
    "goals,learned,expected_output",
    [
        ({}, {}, set()),
        ({"11": True}, {}, {"9", "10", "11", "20", "17"}),
        ({"11": True}, {"9": True}, {"10", "11", "20", "17"}),
    ],
)
def test_get_concepts_to_learn(
    goals: Dict[str, bool], learned: Dict[str, bool], expected_output: Set[str]
):
    assert MapStatus(goals, learned).concepts_to_learn == expected_output


@pytest.mark.parametrize(
    "goals,learned,expected_output",
    [({}, {}, set()), ({"11": True}, {}, {"9", "17"}), ({"11": True}, {"9": True}, {"17"})],
)
def test_get_next_concepts(
    goals: Dict[str, bool], learned: Dict[str, bool], expected_output: Set[str]
):
    assert MapStatus(goals, learned).next_concepts == expected_output


class TestCheckAnswer(TestCase):
    MC = "multiple-choice"

    def test_check_answer_multiple_choice(self):
        check_answer(self.MC, "A", "A", False)
        check_answer(self.MC, "2", "2", False)
        # TODO: Finish this function (use parameterizes)

    # TODO: Finish this class
