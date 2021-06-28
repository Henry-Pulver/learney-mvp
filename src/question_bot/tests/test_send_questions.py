from datetime import date, time, timedelta

import pytest

from question_bot.models import SlackBotUserModel
from question_bot.send_questions import get_days_until_end

TEST_ID = "awgeiubwgr"


@pytest.mark.parametrize("dt", [1, 5, 7, 9, 11])
def test_get_days_until_end(dt: int):
    assert (
        get_days_until_end(
            SlackBotUserModel(
                user_id=TEST_ID,
                relative_question_time=date.today(),
                timezone="GMT + 2",
                utc_time_to_send=time(hour=14, minute=12),
                on_slack=False,
                on_learney=False,
                active_since=date.today() - timedelta(days=dt),
            )
        )
        == 7 - dt
    )
