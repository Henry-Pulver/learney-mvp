import time
from typing import Any, Dict, Tuple

import numpy as np
from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.inference import GaussianParams, MCMCInference
from questions.models import QuestionResponse
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch
from questions.question_selection import MCMC_MUTEX, select_questions

# from silk.profiling.profiler import silk_profile


class QuestionResponseView(APIView):
    # @silk_profile(name="Question Response - Infer Knowledge and Select new Question")
    def post(self, request: Request, format=None) -> Response:
        # try:
        # Extract data from request
        concept_id = request.data["concept_id"]
        user_id = request.data["user_id"]
        question_response_id = request.data["question_response_id"]
        question_batch_id = request.data["question_set"]

        # Save the response in the DB
        q_response: QuestionResponse = cache.get(question_response_id)
        if q_response is None:
            q_response = QuestionResponse.objects.get(id=question_response_id)
        q_response.correct = request.data["correct"]
        q_response.response = request.data["response"]
        # q_response.time_to_respond = request.data["time_to_respond"]
        q_response.save()
        cache.delete(question_response_id)

        q_batch: QuestionBatch = cache.get(question_batch_id)
        if q_batch is None:
            q_batch = (
                QuestionBatch.objects.prefetch_related("user__knowledge_states__concept")
                .prefetch_related("responses__question_template__concept")
                .get(id=question_batch_id)
            )
            cache.set(question_batch_id, q_batch, 600)

        # Get all the precomputed json data from the cache
        q_batch_json = cache.get(f"question_json:{question_batch_id}")
        # And redo the computations now if it's not there!
        if q_batch_json is None:
            q_batch_json = q_batch.json()
        else:
            q_batch_json["answers_given"].append(q_response.response)
        cache.set(f"question_json:{question_batch_id}", q_batch_json)

        # Get data to infer knowledge state
        # difficulties, guess_probs, correct = q_batch.training_data
        difficulties, guess_probs, correct = get_training_data(q_batch_json)

        # If there are multiple processes running numpyro, it errors. So we use this mutex to prevent that.
        while cache.get(MCMC_MUTEX) is not None:
            # The second mutex checks the process holding the first mutex is related to the same user.
            if cache.get(f"{MCMC_MUTEX}_{user_id}") is not None:
                # If it is, we increment this counter of the number of questions to select and
                cache.incr(f"{MCMC_MUTEX}_{user_id}")
                return Response(
                    {"response": "MCMC already in progress"},
                    status=status.HTTP_200_OK,
                )
            else:
                time.sleep(0.25)
        cache.set_many({MCMC_MUTEX: True, f"{MCMC_MUTEX}_{user_id}": 1}, timeout=30)
        # Infer new knowledge state
        mcmc = MCMCInference(q_batch.initial_knowledge_state)
        mcmc.run_mcmc_inference(difficulties=difficulties, guess_probs=guess_probs, answers=correct)
        new_theta = mcmc.inferred_theta_params

        # Update InferredKnowledgeState in the DB
        ks_model: InferredKnowledgeState = cache.get(
            f"InferredKnowledgeState:concept:{concept_id}user:{user_id}"
        )
        if ks_model is None:
            ks_model = InferredKnowledgeState.objects.get(
                user__id=user_id, concept__cytoscape_id=concept_id
            )
        new_ks = GaussianParams(mean=new_theta.mean, std_dev=new_theta.std_dev)
        print(
            f"Previous knowledge state: ({round(ks_model.mean, 2)}, {round(ks_model.std_dev, 2)})"
        )
        print(f"New knowledge state: ({round(new_theta.mean, 2)}, {round(new_theta.std_dev, 2)})")
        ks_model.mean = new_theta.mean
        ks_model.std_dev = new_theta.std_dev
        ks_model.highest_level_achieved = max(ks_model.highest_level_achieved, new_ks.level)
        ks_model.save()
        cache.set(f"InferredKnowledgeState:concept:{concept_id}user:{user_id}", ks_model)

        # Below cache get re-run because it may have been updated by another process!
        q_batch_json = cache.get(f"question_json:{question_batch_id}")
        num_left_to_ask = q_batch_json["max_num_questions"] - len(q_batch_json["answers_given"])
        # Pick new questions to ask
        if num_left_to_ask > 0:
            next_questions = select_questions(
                concept_id=concept_id,
                question_batch=q_batch,
                question_batch_json=q_batch_json,
                user=q_batch.user,
                session_id=request.data["session_id"],
                mcmc=mcmc,
                number_to_select=None if num_left_to_ask > 1 else 1,
            )
        else:
            next_questions = []

        # Release mutex
        cache.delete_many([MCMC_MUTEX, f"{MCMC_MUTEX}_{user_id}"])

        cache.set(f"question_json:{question_batch_id}", q_batch_json, timeout=1200)

        # Is the question_batch completed?
        concept_completed = new_ks.level > q_batch.concept.max_difficulty_level
        num_responses = len(q_batch_json["answers_given"])
        doing_poorly = num_responses >= 5 and new_ks.level < -0.5
        print(f"Number of questions asked: {len(q_batch_json['questions'])}")
        print(f"Number of questions answered: {num_responses}")
        max_num_of_questions_answered = num_responses >= q_batch_json["max_num_questions"]
        # Check it's not a 'revision batch' - if it is, ignore how well they do!
        if q_batch.is_revision_batch:
            completed = "review_completed" if max_num_of_questions_answered else ""
        else:
            completed = (
                "completed_concept"
                if concept_completed
                else "doing_poorly"
                if doing_poorly
                else "max_num_of_questions"
                if max_num_of_questions_answered
                else ""
            )
        if completed:
            print(f"completed: {completed}")
            # Update stored data on the question batch
            q_batch.completed = completed
            q_batch.levels_progressed = new_ks.level - q_batch.initial_knowledge_state.level
            q_batch.concept_completed = concept_completed
            q_batch.save()
            cache.delete(question_batch_id)  # Clear the cache
        # print(q_batch_json)
        return Response(
            {
                "level": ks_model.get_display_knowledge_level(new_batch=False),
                "completed": completed,
                "next_questions": next_questions,
            },
            status=status.HTTP_200_OK,
        )
        # except Exception as e:
        #     return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


def get_training_data(q_batch_json: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Get the training data for the question batch.

    :param q_batch_json: The question batch json.
    :return: The training data.
    """
    responses = q_batch_json["answers_given"]
    questions = q_batch_json["questions"][: len(responses)]
    difficulties = [q["difficulty"] for q in questions]
    guess_probs = [1 / len(q["answers_order_randomised"]) for q in questions]
    correct = [q["correct_answer"] == response for q, response in zip(questions, responses)]
    return np.array(difficulties), np.array(guess_probs), np.array(correct)
