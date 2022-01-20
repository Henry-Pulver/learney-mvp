import re

from django.core.exceptions import ValidationError


def validate_numeric(value: str) -> None:
    if not value.isnumeric():
        raise ValidationError(f"{value} is not a number string!")


def validate_hex_colour(value: str) -> None:
    if not re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", value):
        raise ValidationError(f"{value} is not a valid hex colour!")
