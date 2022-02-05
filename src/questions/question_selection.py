from collections import Counter
from typing import Any, Dict, List, Optional

import numpy as np
from django.core.cache import cache
from django.db.models import Q, QuerySet

from accounts.models import User
from questions.inference import MCMCInference
from questions.models import QuestionResponse, QuestionTemplate
from questions.models.question_batch import QuestionBatch
from questions.template_parser import number_of_questions, parse_params, sample_params
from questions.utils import get_today

# Ideal probability of correct
IDEAL_DIFF = 0.85


def select_question(
    concept_id: str,
    question_batch: QuestionBatch,
    user: User,
    session_id: str,
    mcmc: Optional[MCMCInference] = None,
    save_question_to_db: bool = True,
) -> Dict[str, Any]:
    """Select a question from possible questions for this concept."""
    template_options: List[QuestionTemplate] = list(
        QuestionTemplate.objects.filter(concept__cytoscape_id=concept_id, active=True)
    )
    print(f"template_options: {template_options}")
    assert (
        len(template_options) > 0
    ), f"No template options to choose from for concept with cytoscape id: {concept_id}!"

    # If no mcmc object provided, make one (providing one speeds up inference by using past samples)
    mcmc = mcmc or MCMCInference(
        user.knowledge_states.all().get(concept__cytoscape_id=concept_id).knowledge_state
    )
    # Calculate the weights. Once normalised, these form the categorical
    #  distribution over question templates
    difficulty_terms = get_difficulty_terms(template_options, mcmc)
    print(f"difficulty_terms: {difficulty_terms}")
    novelty_terms = get_novelty_terms(template_options, user, question_batch)
    print(f"Novelty terms: {novelty_terms}")
    question_weights = difficulty_terms * novelty_terms

    # Choose the template that's going to be used!
    chosen_template: QuestionTemplate = np.random.choice(
        template_options, p=question_weights / np.sum(question_weights)
    )
    print(
        f"Chosen template: {chosen_template}, number of questions: {number_of_questions(chosen_template.template_text)}"
    )
    question_param_options = parse_params(chosen_template.template_text)
    # Avoid sampling parameters for this template already seen in this question batch!
    params_to_avoid = [
        p["question_params"]
        for p in question_batch.responses.filter(question_template=chosen_template).values(
            "question_params"
        )
    ]
    sampled_params = sample_params(question_param_options, params_to_avoid)

    response_id = ""
    if save_question_to_db:  # Track the question was sent in the DB
        q_response = QuestionResponse.objects.create(
            user=user,
            question_template=chosen_template,
            question_params=sampled_params,
            question_batch=question_batch,
            predicted_prob_correct=mcmc.correct_probs[template_options.index(chosen_template)],
            session_id=session_id,
            time_to_respond=None,
        )
        response_id = q_response.id
        cache.set(q_response, q_response.id)

    return chosen_template.to_question_json(response_id, sampled_params)


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
    template_options: List[QuestionTemplate], user: User, question_batch: QuestionBatch
) -> np.ndarray:
    """Calculate the novelty terms for all template options to weight different templates."""
    questions_to_avoid: QuerySet[QuestionResponse] = (
        user.responses.all()
        .filter(
            Q(time_asked__gte=get_today()) | Q(correct=True),
            question_template__concept__cytoscape_id=question_batch.concept.cytoscape_id,
        )  # Questions asked today or answered correct ever on this concept
        .select_related("question_batch")
        .select_related("question_template")
    )

    batch_q_types = [
        question.question_template.question_type for question in question_batch.responses.all()
    ]
    q_type_counter = Counter(batch_q_types)

    output = cache.get(f"novelty_terms_{question_batch.id}")
    if output:
        most_recent_question_template = (
            question_batch.responses.all().latest("time_asked").question_template
        )
        output[template_options.index(most_recent_question_template)] = calculate_novelty(
            most_recent_question_template, questions_to_avoid, question_batch, q_type_counter
        )
    else:
        output = [
            calculate_novelty(option, questions_to_avoid, question_batch, q_type_counter)
            for option in template_options
        ]
    cache.set(f"novelty_terms_{question_batch.id}", output)

    return np.array(output)


def calculate_novelty(
    template: QuestionTemplate,
    questions_to_avoid: QuerySet[QuestionResponse],
    question_batch: QuestionBatch,
    q_type_counter: Counter,
) -> float:
    n_qs = number_of_questions(template.template_text)
    novelty_term = 1

    # [1.0] Avoid questions on the same template
    template_qs_to_avoid = questions_to_avoid.filter(question_template__id=template.id)

    # [1.1] Worst are questions from the same batch - avoid like the plague
    batch_qs_to_avoid = template_qs_to_avoid & question_batch.responses.all()
    num_batch_qs_to_avoid = batch_qs_to_avoid.count()
    if num_batch_qs_to_avoid > 0:
        # Weight by the sqrt of the number of questions (n_qs) generated from a template
        novelty_term *= np.exp(-5 * num_batch_qs_to_avoid / np.sqrt(n_qs))
        template_qs_to_avoid.difference(batch_qs_to_avoid)

    # [1.2] Then there are questions asked today or correct from the past
    distinct_qs_asked = template_qs_to_avoid.count()
    novelty_term *= 0.9 * np.exp(-2.5 * distinct_qs_asked / n_qs) + 0.1

    # [2.0] Lastly avoid giving all the same type of question in a batch
    num_batch_q_types = sum(q_type_counter.values())
    if num_batch_q_types > 3:
        novelty_term *= 1 - np.exp(
            -10 * ((q_type_counter[template.question_type] / num_batch_q_types) - 1) + 0.1
        )
    return novelty_term
