from typing import Any

from django.core.exceptions import ValidationError


def integer_is_positive(integer: int) -> None:
    if integer < 0:
        raise ValidationError("Value isn't positive!")


def not_null(value: str) -> None:
    if not value:
        raise ValidationError("Value is null!")


def ensure_list(value: Any) -> None:
    if not isinstance(value, list):
        raise ValidationError("Value is not a list!")
