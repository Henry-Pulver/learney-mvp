from django.core.exceptions import ValidationError


def validate_numeric(value: str) -> None:
    if not value.isnumeric():
        raise ValidationError(f"{value} is not a number string!")
