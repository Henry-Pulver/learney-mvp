from datetime import date, time, timedelta

import pytest

from question_bot.models import SlackBotUserModel
from question_bot.send_questions import get_days_until_end

TEST_EMAIL = "awgeiubwgr"


@pytest.mark.parametrize("dt,duration", [(1, 3), (5, 7), (7, 1), (9, 6), (11, 17)])
def test_get_days_until_end(dt: int, duration: int):
    assert (
        get_days_until_end(
            SlackBotUserModel(
                user_email=TEST_EMAIL,
                relative_question_time=date.today(),
                timezone="GMT + 2",
                utc_time_to_send=time(hour=14, minute=12),
                on_slack=False,
                on_learney=False,
                active_since=date.today() - timedelta(days=dt),
            ),
            duration,
        )
        == duration - dt
    )
