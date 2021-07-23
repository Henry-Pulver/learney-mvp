import enum
from typing import Optional


class DifficultyChange(enum.Enum):
    too_easy = -1
    bored = 0
    too_hard = 1


def string_to_difficulty(difficulty_change_string: str) -> Optional[DifficultyChange]:
    if difficulty_change_string.lower() == "too easy":
        return DifficultyChange.too_easy
    elif difficulty_change_string.lower() == "bored":
        return DifficultyChange.bored
    elif difficulty_change_string.lower() == "too hard":
        return DifficultyChange.too_easy
    else:
        return None
