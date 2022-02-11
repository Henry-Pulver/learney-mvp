from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from django.core.cache import cache
from django.db.models import Q, QuerySet

from accounts.models import User
from questions.inference import MCMCInference
from questions.models import QuestionResponse, QuestionTemplate
from questions.models.question_batch import QuestionBatch
from questions.template_parser import (
    check_valid_params_exist,
    number_of_questions,
    parse_params,
    sample_params,
)
from questions.utils import SampledParamsDict, get_today

# Ideal probability of correct
IDEAL_DIFF = 0.85

MCMC_MUTEX = "MCMC_MUTEX"


def select_questions(
    concept_id: str,
    question_batch_json: Dict[str, Any],
    user: User,
    session_id: str,
    mcmc: Optional[MCMCInference] = None,
    save_question_to_db: bool = True,
    number_to_select: Optional[int] = None,
    question_batch: Optional[QuestionBatch] = None,
) -> List[Dict[str, Any]]:
    """Select questions from possible questions for this concept."""
    assert (
        number_to_select is None or number_to_select > 0
    ), f"{number_to_select} is not a valid number of questions"
    template_options: List[QuestionTemplate] = cache.get(f"template_options_{concept_id}")
    if template_options is None:
        template_options = list(
            QuestionTemplate.objects.filter(concept__cytoscape_id=concept_id, active=True)
        )
        cache.set(f"template_options_{concept_id}", template_options, timeout=60 * 60 * 24)
    assert (
        len(template_options) > 0
    ), f"No template options to choose from for concept with cytoscape id: {concept_id}!"

    # If no mcmc object provided, make one (providing one speeds up inference by using past samples)
    ks = cache.get(f"InferredKnowledgeState:concept:{concept_id}user:{user.id}")
    mcmc = mcmc or MCMCInference(
        ks.knowledge_state
        if ks
        else user.knowledge_states.all().get(concept__cytoscape_id=concept_id).knowledge_state
    )

    # Calculate the weights. Once normalised, these form the categorical
    #  distribution over question templates
    difficulty_terms = get_difficulty_terms(template_options, mcmc)
    print(f"difficulty_terms: {difficulty_terms}")
    questions_chosen: List[Dict[str, Any]] = []
    # Check cache for number of extra questions to select if number_to_select not provided. If both None, select 1
    print(
        f"number_to_select: {number_to_select}\tcache.get(): {cache.get(f'{MCMC_MUTEX}_{user.id}')}"
    )
    while len(questions_chosen) < (number_to_select or cache.get(f"{MCMC_MUTEX}_{user.id}") or 1):
        novelty_terms = get_novelty_terms(template_options, user, question_batch_json, concept_id)
        print(f"Novelty terms: {novelty_terms}")
        question_weights = difficulty_terms * novelty_terms
        # nan_to_num converts very small nans to 0
        question_probs = np.nan_to_num(question_weights / np.sum(question_weights))

        # Choose the template that's going to be used!
        question_chosen = None
        while question_chosen is None:
            valid_params_exist = False
            while not valid_params_exist:
                chosen_template: QuestionTemplate = np.random.choice(
                    template_options, p=question_probs
                )
                print(
                    f"Chosen template: {chosen_template}, num of qs: {number_of_questions(chosen_template.template_text)}"
                )
                # Avoid sampling parameters for this template already seen in this question batch!
                params_to_avoid: List[SampledParamsDict] = [
                    question["params"]
                    for question in question_batch_json["questions"]
                    if question["template_id"] == chosen_template.id
                ]
                valid_params_exist = check_valid_params_exist(
                    param_options=parse_params(chosen_template.template_text),
                    params_to_avoid=params_to_avoid,
                )
            question_chosen = chosen_template.to_question_json(params_to_avoid=params_to_avoid)

        if save_question_to_db:  # Track the question was sent in the DB
            if question_batch is None:
                question_batch = cache.get(question_batch_json["id"])
                if question_batch is None:
                    question_batch = QuestionBatch.objects.get(id=question_batch_json["id"])
            q_response = QuestionResponse.objects.create(
                user=user,
                question_template=chosen_template,
                question_params=question_chosen["params"],
                question_batch=question_batch,
                predicted_prob_correct=mcmc.correct_probs[template_options.index(chosen_template)],
                session_id=session_id,
                time_to_respond=None,
            )
            print(f"New response_id: {q_response.id}")
            question_chosen["id"] = q_response.id
            # Cache for use when question is answered
            cache.set(q_response.id, q_response, timeout=120)

        # print(f"question_chosen: {question_chosen}")
        questions_chosen.append(question_chosen)
        question_batch_json["questions"].append(question_chosen)

    return questions_chosen


def prob_correct_to_weighting(correct_probs: np.ndarray) -> np.ndarray:
    """Weighting curve taking probabilities of getting each question correct and outputting the
    difficulty weighting."""
    assert np.all(correct_probs >= 0) and np.all(
        correct_probs <= 1
    ), f"{correct_probs} is not a valid probability value (0<= p <=1)"
    # Below is `std_dev = 0.3 if < IDEAL_DIFF else 0.08` in numpy
    std_dev = 0.22 * (correct_probs <= IDEAL_DIFF) + 0.08
    return np.exp(-(1 / 2) * (((correct_probs - IDEAL_DIFF) / std_dev) ** 2))


def get_difficulty_terms(
    template_options: List[QuestionTemplate],
    mcmc: MCMCInference,
) -> np.array:
    """Calculate 'difficulty' terms for all template options to weight different templates."""
    guess_probs = np.array([1 / template.number_of_answers for template in template_options])
    difficulties = np.array([template.difficulty for template in template_options])
    correct_probs = mcmc.calculate_correct_probs(difficulties=difficulties, guess_probs=guess_probs)
    return prob_correct_to_weighting(correct_probs)


def get_novelty_terms(
    template_options: List[QuestionTemplate],
    user: User,
    question_batch_json: Dict[str, Any],
    concept_id: str,
) -> np.ndarray:
    """Calculate the novelty terms for all template options to weight different templates."""
    data_from_questions_to_avoid: List[Dict[str, Union[UUID, str]]] = cache.get(
        f"data_from_questions_to_avoid_{question_batch_json['id']}"
    )
    if data_from_questions_to_avoid is None:
        data_from_questions_to_avoid = list(
            QuestionResponse.objects.filter(
                Q(time_asked__gte=get_today()) | Q(correct=True),
                user=user,
                question_template__concept__cytoscape_id=concept_id,
            ).values("id", "question_template__question_type")
        )  # Questions asked today or answered correct ever on this concept

    novelty_terms = cache.get(f"novelty_terms_{question_batch_json['id']}")
    if novelty_terms is not None:
        # This is the most recently chosen template's id
        prev_template_id = question_batch_json["questions"][-1]["template_id"]
        prev_template_index = int(
            np.where([t.id == prev_template_id for t in template_options])[0][0]
        )
        novelty_terms[prev_template_index] = calculate_novelty(
            template_options[prev_template_index], data_from_questions_to_avoid, question_batch_json
        )
    else:
        novelty_terms = [
            calculate_novelty(option, data_from_questions_to_avoid, question_batch_json)
            for option in template_options
        ]
    cache.set(f"novelty_terms_{question_batch_json['id']}", novelty_terms)
    array_output = np.array(novelty_terms)
    assert np.any(
        array_output >= 0
    ), f"All novelty terms are 0, thus all questions have been seen before ({array_output})"

    return array_output


def calculate_novelty(
    template: QuestionTemplate,
    q_template_data_to_avoid: List[Dict[str, Union[UUID, str]]],
    q_batch_json: Dict[str, Any],
) -> float:
    n_qs = number_of_questions(template.template_text)
    novelty_term = 1

    # [1.0] Avoid questions on the same template
    num_batch_qs_on_this_template = sum(
        q["template_id"] == template.id for q in q_batch_json["questions"]
    )

    # [1.1] Worst are questions from the same batch - avoid like the plague
    if num_batch_qs_on_this_template > 0:
        # Weight by the sqrt of the number of questions (n_qs) generated from a template
        novelty_term *= np.exp(-2.5 * num_batch_qs_on_this_template / np.sqrt(n_qs))

    # [1.2] Then there are questions asked today or correct from the past
    num_template_qs_to_avoid = (
        sum(t_data["id"] == template.id for t_data in q_template_data_to_avoid)
        - num_batch_qs_on_this_template
    )
    novelty_term *= 0.6 * np.exp(-2.5 * num_template_qs_to_avoid / n_qs) + 0.4

    # [2.0] Lastly avoid giving all the same type of question in a batch
    num_questions_asked = len(q_batch_json["questions"])
    if num_questions_asked > 3:
        novelty_term *= (
            0.6
            * np.exp(
                -(
                    2
                    * sum(
                        q["question_type"] == template.question_type
                        for q in q_batch_json["questions"]
                    )
                    / num_questions_asked
                )
            )
            + 0.4
        )
    return novelty_term
