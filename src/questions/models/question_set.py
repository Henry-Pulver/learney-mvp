from typing import Any, Dict, Tuple

import numpy as np
from django.db import models

from accounts.models import User
from learney_backend.base_models import UUIDModel
from questions.inference import GaussianParams


class QuestionSet(UUIDModel):
    user = models.ForeignKey(
        User,
        related_name="question_responses",
        help_text="User whose response this is",
        on_delete=models.CASCADE,
    )

    time_started = models.DateTimeField(
        auto_now_add=True, help_text="Time that the question set was started"
    )
    time_taken_to_complete = models.DateTimeField(
        null=True,
        default=None,
        help_text="Time after the question set was started that it was completed",
    )
    completed = models.BooleanField(
        default=False, help_text="Whether the user answered all the questions in the set or not"
    )
    level_at_start = models.IntegerField(
        help_text="The concept level the user started the question set at"
    )
    initial_knowledge_mean = models.FloatField(
        help_text="Mean of the user's knowledge state when they started the question set"
    )
    initial_knowledge_std_dev = models.FloatField(
        help_text="Standard deviation of the user's knowledge state when they started the question set"
    )
    levels_progressed = models.IntegerField(
        default=0, help_text="How many levels the user progressed in this question batch"
    )
    concept_completed = models.BooleanField(
        default=False,
        help_text="Whether the highest level of the concept was achieved in this question set",
    )
    session_id = models.TextField(help_text="session_id of the session the response was from")

    def json(self) -> Dict[str, Any]:
        responses = self.responses.all().select_related("question_template__concept")
        return {
            "id": self.id,
            "questions": [response.json for response in responses],
            "answers_given": [response.response for response in responses],
            "completed": self.completed,
            "concept_id": responses[0].concept.cytoscape_id,
        }

    @property
    def training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        difficulties = np.array([response.template.difficulty for response in self.responses])
        guess_probs = np.array(
            [1 / response.template.number_of_answers for response in self.responses]
        )
        correct = np.array([response.correct for response in self.responses])
        return difficulties, guess_probs, correct

    @property
    def initial_knowledge_state(self) -> GaussianParams:
        return GaussianParams(
            mean=self.initial_knowledge_mean, std_dev=self.initial_knowledge_std_dev
        )
