from collections import Counter
from typing import Any, Dict, List, Optional

import numpy as np
from django.db.models import Q

from accounts.models import User
from questions.inference import MCMCInference
from questions.models import QuestionTemplate
from questions.models.question_set import QuestionSet
from questions.template_parser import number_of_questions, parse_params, sample_params
from questions.utils import get_today

# Ideal probability of correct
IDEAL_DIFF = 0.85


def select_question(
    concept_id: str,
    question_set: QuestionSet,
    user: User,
    mcmc: Optional[MCMCInference] = None,
) -> Dict[str, Any]:
    """Select a question from possible questions for this concept."""
    template_options = QuestionTemplate.objects.filter(
        concept__cytoscape_id=concept_id, active=True
    ).prefetch_related("responses")

    # If no mcmc object provided (this speeds up inference), make one
    mcmc = mcmc or MCMCInference(
        user.knowledge_states.all().get(concept__cytoscape_id=concept_id).knowledge_state
    )
    # Calculate the weights. Once normalised, these form the categorical
    #  distribution over question templates
    question_weights = difficulty_terms(template_options, mcmc) * novelty_terms(
        template_options, user, question_set
    )

    # Choose the template that's going to be used!
    question_seen_before = True
    while question_seen_before:
        chosen_template = np.random.choice(
            template_options, p=question_weights / np.mean(question_weights)
        )
        question_param_options, remaining_text = parse_params(chosen_template.template_text)
        sampled_params = sample_params(question_param_options)
        # Make 100% sure it's not been seen already in this question set!
        question_seen_before = question_set.responses.filter(
            question_template=chosen_template, question_params=sampled_params
        ).exists()

    return chosen_template.to_question_json(sampled_params)


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
    template_options: List[QuestionTemplate],
    mcmc: MCMCInference,
) -> np.array:
    """Calculate 'difficulty' terms for all template options to weight different templates."""
    guess_probs = np.array([1 / template.number_of_answers for template in template_options])
    difficulties = np.array([template.difficulty for template in template_options])
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
