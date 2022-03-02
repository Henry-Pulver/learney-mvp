import random
import warnings
from typing import Any, Dict, List, Optional, Tuple

from django.db import models

from knowledge_maps.models import Concept
from learney_backend.base_models import UUIDModel
from questions.template_parser import (
    answer_regex,
    expand_params_in_text,
    is_param_line,
    parse_params,
    remove_start_and_end_newlines,
    sample_params,
    says_feedback,
)
from questions.utils import SampledParamsDict
from questions.validators import integer_is_positive, not_null

PREREQ_QUESTION_DIFF = 0.25


class QuestionTemplate(UUIDModel):
    title = models.CharField(max_length=255, help_text="The title of the question template.")
    concept = models.ForeignKey(
        Concept,
        related_name="question_templates",
        help_text="Concept that the question corresponds to",
        on_delete=models.CASCADE,
    )
    difficulty = models.FloatField(
        help_text="Question difficulty for the concept. Initially set by an expert, but will "
        "subsequently be inferred from data. A relative scale, with 0 the lowest "
        "possible and as many difficulty levels as is deemed makes sense by the expert.",
        validators=[integer_is_positive],
    )
    question_type = models.CharField(
        help_text="Type of question - used to pick questions which vary in type",
        choices=[("conceptual", "Conceptual"), ("practice", "Practice"), ("", "No type")],
        max_length=20,
    )

    template_text = models.TextField(
        help_text="Text for question template - generates full questions",
        blank=False,
        validators=[not_null],
        max_length=16384,
    )
    correct_answer_letter = models.CharField(
        max_length=1,
        help_text="Answer option (a, b, c or d) which is the correct answer to the question",
        choices=[
            ("a", "Option a)"),
            ("b", "Option b)"),
            ("c", "Option c)"),
            ("d", "Option d)"),
        ],
        blank=False,
    )
    active = models.BooleanField(
        default=False,
        help_text="If questions from the template should be used on the live site - "
        "broken questions should be deactivated until they're fixed!",
    )
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def number_of_answers(self) -> int:
        num_answers = sum(
            answer_regex(line) is not None for line in self.template_text.splitlines()
        )
        assert num_answers in [
            2,
            4,
        ], f"Invalid number of answers ({num_answers}) for {self.id}. Template:\n{self.template_text}"
        return num_answers

    def to_question_json(
        self,
        sampled_params: Optional[SampledParamsDict] = None,
        params_to_avoid: Optional[List[SampledParamsDict]] = None,
        prerequisite_concept: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Gets question dictionary from a template and set of sampled parameters.

        If a question can't be generated, return None.
        """
        for _ in range(1000):  # This loop is to ensure that multiple answers aren't identical
            if sampled_params is None:
                parsed_params = parse_params(self.template_text)
                sampled_params = sample_params(parsed_params, params_to_avoid)
                if sampled_params is None:
                    return None
            text_expanded = expand_params_in_text(self.template_text, sampled_params)

            question_text, feedback, answers = parse_template(text_expanded)

            answers_order_randomised = list(answers.values())
            # For many question templates, it's possible that 2 answers are the same.
            # This is a problem because users need to have different answers to pick from!
            if self.answers_all_different(answer_list=answers_order_randomised):
                random.shuffle(answers_order_randomised)
                return {
                    "title": self.title,
                    "template_id": self.id,
                    "question_text": remove_start_and_end_newlines(question_text),
                    "question_type": self.question_type,
                    "answers_order_randomised": answers_order_randomised,
                    "correct_answer": answers[self.correct_answer_letter],
                    "feedback": remove_start_and_end_newlines(feedback),
                    "difficulty": self.difficulty
                    if not prerequisite_concept
                    else PREREQ_QUESTION_DIFF,
                    "params": sampled_params,
                }
            sampled_params = None  # Try again with new params
        warnings.warn(f"Could not ensure all answers are different for {self.id} after 1000 tries.")
        return None

    @staticmethod
    def answers_all_different(answer_list: List[str]) -> bool:
        """Checks if all answers are different."""
        answer_list_without_spaces = [answer.replace(" ", "") for answer in answer_list]
        return len(set(answer_list_without_spaces)) == len(answer_list_without_spaces)

    def __str__(self):
        return f"{self.id} on {self.concept.cytoscape_id}, {self.question_type}"


def parse_template(text: str) -> Tuple[str, str, Dict[str, str]]:
    answers: Dict[str, str] = {}
    question_text, feedback, is_feedback, current_answer = "", "", False, ""
    for line in text.splitlines():
        if not is_param_line(line):  # Ignore param lines
            is_feedback = is_feedback or says_feedback(line)
            regex = answer_regex(line)
            # Allow for answers spanning multiple lines - remember if it's on an answer from previous line
            current_answer = (
                regex.groups()[0].lower()
                if (regex is not None)
                else current_answer
                if not is_feedback
                else ""
            )
            if not current_answer and not is_feedback:
                question_text += line + "\n"
            elif current_answer:
                # Add new line to prev line if answer spans multiple lines
                prev_answer_line = (
                    f"{current_answer}) {answers[current_answer]}"
                    if answers.get(current_answer)
                    else ""
                )
                regex = answer_regex(prev_answer_line + line)
                assert (
                    regex is not None
                ), f"This is a bug. This should enInvalid answer line: {prev_answer_line + line}"
                answers[current_answer] = regex.groups()[1]
            elif is_feedback and not says_feedback(line):  # skip the word 'feedback'
                feedback += line + "\n"

    # Remove zero width spaces
    question_text = question_text.replace("\u200b", "")
    feedback = feedback.replace("\u200b", "")
    answers = {key: value.replace("\u200b", "") for key, value in answers.items()}

    return question_text, feedback, answers
