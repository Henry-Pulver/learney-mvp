import enum
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Dict, List, Set, Tuple

import numpy as np
from django.db.models.query import QuerySet

from goals.models import GoalModel
from knowledge_maps.orig_map_uuid import ORIG_MAP_UUID
from learned.models import LearnedModel
from learney_web import settings
from page_visits.models import PageVisitModel


class AnswerOutcome(enum.Enum):
    try_again = -2
    passed = -1
    incorrect = 0
    correct = 1


def get_first_name(slack_response: Dict) -> str:
    return slack_response["user"]["profile"].get(
        "first_name", slack_response["user"]["real_name"].split(" ")[0]
    )


def check_answer(
    answer_type: str, answer_given: str, correct_answer: str, allow_again: bool
) -> AnswerOutcome:
    """Checks the answer given through Slack.

    Args:
        answer_type: Type of answer we're expecting (eg multiple-choice, yes/no)
        answer_given: The answer given by the student
        correct_answer: The correct answer we're checking the student did (or didn't) get
        allow_again: whether to allow returning None (give the learner another go)

    Returns: Whether the answer is correct, incorrect or if we think they should try again
    """
    if answer_given.lower() == "pass":
        return AnswerOutcome.passed
    elif answer_type.lower() == "yes/no":
        if len(answer_given) > 3:
            return AnswerOutcome.try_again if allow_again else AnswerOutcome.incorrect
        else:
            return (
                AnswerOutcome.correct
                if answer_given.lower() == correct_answer.lower()
                else AnswerOutcome.incorrect
            )
    elif answer_type.lower() == "multiple-choice":
        answer_given.replace(" ", "")  # ignore spaces
        # If over 3 char response to a multiple-choice q, something has gone wrong
        if len(answer_given) > 3:
            return AnswerOutcome.try_again if allow_again else AnswerOutcome.incorrect
        elif correct_answer.isnumeric():
            if correct_answer in answer_given:
                number_count = sum([char.isnumeric() for char in answer_given])
                return AnswerOutcome.correct if number_count == 1 else AnswerOutcome.try_again
            else:
                return AnswerOutcome.incorrect
        elif correct_answer.isalpha():
            if correct_answer.lower() in answer_given.lower():
                if correct_answer in answer_given:  # Check given answer contains the correct answer
                    alphabetic_count = sum([char.isalpha() for char in answer_given])
                    return (
                        AnswerOutcome.correct if alphabetic_count == 1 else AnswerOutcome.try_again
                    )
                else:
                    return AnswerOutcome.incorrect
            else:
                return AnswerOutcome.incorrect
        else:
            raise NotImplementedError(
                f"Non-alphanumeric answers such as {correct_answer} aren't supported in multiple-choice!"
            )
    elif answer_type.lower() == "numeric answer":
        return (
            AnswerOutcome.correct
            if np.isclose(
                numeric_answer_to_float(correct_answer),
                numeric_answer_to_float(answer_given),
            )
            else AnswerOutcome.incorrect
        )
    else:
        raise NotImplementedError(f"Answer type {answer_type} is not supported!")


def numeric_answer_to_float(answer: str):
    if "/" in answer:  # fraction
        return float(answer.split("/")[0]) / float(answer.split("/")[1])
    else:
        return float(answer)


def get_nearest_half_hour(t: time):
    rounded_hour = round(t.hour + (t.minute - 15) / 60) % 24
    return time(rounded_hour, 30 * (round((t.minute + t.second / 60) / 30) % 2))


def get_utc_time_to_send(time_str: str, time_difference_str: str) -> time:
    time_dif_magnitude = int(time_difference_str[-2:])
    time_difference = time_dif_magnitude * -1 if "+" in time_difference_str else time_dif_magnitude
    relative_time = datetime.strptime(time_str, "%H:%M")
    return time(hour=(relative_time.hour + time_difference) % 24, minute=relative_time.minute)


@dataclass
class MapStatus:
    # Inputs
    goal_dict: Dict[str, bool]
    learned_dict: Dict[str, bool]

    learned_concepts: Set[str] = field(init=False)
    goals: Set[str] = field(init=False)
    concepts_to_learn: Set[str] = field(init=False)
    next_concepts: Set[str] = field(init=False)

    def __post_init__(self) -> None:
        self.learned_concepts = {id for id, is_learned in self.learned_dict.items() if is_learned}
        self.goals = {goal for goal, is_goal in self.goal_dict.items() if is_goal}
        self.concepts_to_learn = self.get_concepts_to_learn()
        self.next_concepts = self.get_next_concepts()

    # @property
    def get_next_concepts(self) -> Set[str]:
        immediate_next_concepts = set()
        for concept_to_learn in self.concepts_to_learn:
            # No predecessors
            if concept_to_learn not in settings.ORIG_MAP_PREDECESSOR_DICT:
                immediate_next_concepts.add(concept_to_learn)
            # All predecessors must be known
            elif all(
                [
                    pre in self.learned_concepts
                    for pre in settings.ORIG_MAP_PREDECESSOR_DICT[concept_to_learn]
                ]
            ):
                immediate_next_concepts.add(concept_to_learn)
        return immediate_next_concepts

    def get_concepts_to_learn(self) -> Set[str]:
        current_nodes = self.goals
        to_learn = copy(self.goals)
        while len(current_nodes) > 0:
            predecessor_nodes = set()
            for current_node in current_nodes:
                predecessor_nodes.update(
                    settings.ORIG_MAP_PREDECESSOR_DICT.get(current_node, set())
                )
            to_learn.update(predecessor_nodes)
            current_nodes = predecessor_nodes
        return to_learn.difference(self.learned_concepts)


def get_concepts_asked_about(last_set_of_questions: QuerySet) -> List[Tuple[str, int]]:
    """Get the concepts asked about from the last set of questions, ranked by how often they show
    up."""
    concept_counter: Dict[str, int] = {}
    for question_dict in last_set_of_questions.values("question_id"):
        if question_dict["question_id"].split("_")[0] in concept_counter:
            concept_counter[question_dict["question_id"].split("_")[0]] += 1
        else:
            concept_counter[question_dict["question_id"].split("_")[0]] = 1
    return sorted([(q_id, count) for q_id, count in concept_counter.items()], key=lambda x: -x[1])


def is_on_learney(user_email: str) -> bool:
    page_visit_logged = (
        PageVisitModel.objects.filter(map_uuid=ORIG_MAP_UUID, user_id=user_email).count() > 0
    )
    if not page_visit_logged:
        goal_set = GoalModel.objects.filter(map_uuid=ORIG_MAP_UUID, user_id=user_email).count() > 0
        if not goal_set:
            return (
                LearnedModel.objects.filter(map_uuid=ORIG_MAP_UUID, user_id=user_email).count() > 0
            )
    return True
