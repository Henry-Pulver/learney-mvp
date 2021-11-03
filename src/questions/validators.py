from typing import Any

from django.core.exceptions import ValidationError


def not_null(value: str) -> None:
    if not value:
        raise ValidationError("Value is null!")


def ensure_list(value: Any) -> None:
    if not isinstance(value, list):
        raise ValidationError("Value is not a list!")
