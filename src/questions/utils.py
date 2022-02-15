from datetime import datetime
from typing import Dict

SampledParamsDict = Dict[str, str]


def get_today() -> datetime:
    return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
