import math
from collections import Counter
from statistics import NormalDist
from typing import List

import numpy as np
from django.db.models import Max, Q

from accounts.models import User
from knowledge_maps.models import Concept
from questions.inference import MCMCInference
from questions.models import QuestionTemplate
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_set import QuestionSet
from questions.template import get_number_of_answers, number_of_questions
from questions.utils import get_today

# Ideal probability of correct
IDEAL_DIFF = 0.85


def prob_correct_to_weighting(correct_probs: np.ndarray) -> np.ndarray:
    """Weighting curve taking probabilities of getting each question correct and outputting the
    difficulty weighting."""
    assert np.all(correct_probs >= 0) and np.all(
        correct_probs <= 1
    ), f"{correct_probs} is not a valid probability value (0<= p <=1)"
    # Below is `std_dev = 0.3 if < IDEAL_DIFF else 0.08` in numpy
    std_dev = 0.22 * (correct_probs <= IDEAL_DIFF) + 0.08
    return np.exp(-(1 / 2) * (((correct_probs - IDEAL_DIFF) / std_dev) ** 2))


def difficulty_terms(
    template_options: List[QuestionTemplate], knowledge_state: InferredKnowledgeState
) -> np.array:
    """Calculate 'difficulty' terms for all template options to weight different templates."""
    guess_probs = np.array(
        [1 / get_number_of_answers(template.template_text) for template in template_options]
    )
    difficulties = np.array([template.difficulty for template in template_options])
    mcmc = MCMCInference(knowledge_state.knowledge_state)
    prob_correct = mcmc.prob_correct(difficulties=difficulties, guess_probs=guess_probs)
    return prob_correct_to_weighting(prob_correct)


def novelty_terms(
    template_options: List[QuestionTemplate], user: User, question_set: QuestionSet
) -> np.ndarray:
    """Calculate the novelty terms for all template options to weight different templates."""
    output = []
    num_of_questions = [
        number_of_questions(template.template_text) for template in template_options
    ]
    questions_to_avoid = (
        user.responses.all()
        .filter(Q(time_asked__gte=get_today()) | Q(correct=True))
        .select_related("question_set")
        .select_related("question_template")
    )

    set_q_types = [question.question_type for question in question_set.responses]
    q_type_counter = Counter(set_q_types)

    for option, n_qs in zip(template_options, num_of_questions):
        novelty_term = 1

        # [1.0] Avoid questions on the same template
        template_qs_to_avoid = questions_to_avoid.filter(question_template__id=option.id)

        # [1.1] Worst are questions from the same set - avoid like the plague
        set_qs_to_avoid = template_qs_to_avoid.intersection(question_set)
        num_set_qs_to_avoid = set_qs_to_avoid.count()
        if num_set_qs_to_avoid > 0:
            novelty_term *= 0.99 * np.exp(-5 * num_set_qs_to_avoid / n_qs) + 0.01
            template_qs_to_avoid.exclude(set_qs_to_avoid)

        # [1.2] Then are questions asked today or correct from the past
        distinct_qs_asked = (
            template_qs_to_avoid.filter(correct=True).distinct("question_params").count()
        )
        novelty_term *= 0.9 * np.exp(-2.5 * distinct_qs_asked / n_qs) + 0.1

        # [2.0] Lastly avoid giving all the same type of question in a set
        novelty_term *= 1 - np.exp(
            10 * ((q_type_counter[option.question_type] / len(set_q_types)) - 1)
        )

        output.append(novelty_term)

    return np.array(output)


# TODO: Find a new home - this probably shouldn't live here
def get_knowledge_level(knowledge_state: InferredKnowledgeState) -> int:
    ks = knowledge_state.knowledge_state
    return math.floor(NormalDist(mu=ks.mean, sigma=ks.std_dev).inv_cdf(0.05))


def get_max_difficulty_level(concept: Concept) -> int:
    """Gets the highest difficulty of any question on a concept."""
    return concept.responses.all().aggregate(Max("difficulty"))["difficulty"]
