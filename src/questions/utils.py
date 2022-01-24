import json
from typing import Any, Dict, Tuple
from uuid import UUID

from questions.models import QuestionTemplateModel

ParamsDict = Dict[str, Any]


def get_frontend_id(template: QuestionTemplateModel, params_dict: ParamsDict) -> str:
    return f"{params_dict}|{template.id}"


def uuid_and_params_from_frontend_id(frontend_id: str) -> Tuple[UUID, ParamsDict]:
    params_string, template_id = frontend_id.split("|")
    return UUID(template_id), json.loads(params_string) if params_string else {}
