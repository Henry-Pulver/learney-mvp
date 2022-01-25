import json
from datetime import datetime
from typing import Dict, Tuple
from uuid import UUID

SampledParamsDict = Dict[str, str]


def get_today():
    return datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)


def get_frontend_id(template_id: UUID, params_dict: SampledParamsDict) -> str:
    return f"{params_dict}|{template_id}"


def uuid_and_params_from_frontend_id(frontend_id: str) -> Tuple[UUID, SampledParamsDict]:
    params_string, template_id = frontend_id.split("|")
    return UUID(template_id), json.loads(params_string) if params_string else {}
