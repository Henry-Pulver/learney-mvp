import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pytz
from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from learney_web.settings import IS_PROD, mixpanel
from questions.inference import GaussianParams, MCMCInference
from questions.models import QuestionResponse
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.question_batch_cache_manager import QuestionBatchCacheManager
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

        qb_cache_manager = QuestionBatchCacheManager(question_batch_id)
        qb_cache_manager.add_question_answered(q_response)

        # Get data to infer knowledge state
        # difficulties, guess_probs, correct = q_batch.training_data
        difficulties, guess_probs, correct = get_training_data(qb_cache_manager.q_batch_json)

        # Track on mixpanel
        if IS_PROD:
            mixpanel.track(
                request.data["user_id"],
                "Question Answered",
                {
                    "concept_id": concept_id,
                    "Question Batch ID": question_batch_id,
                    "Question Response ID": question_response_id,
                    "Correct": request.data["correct"],
                    "Answer Given": request.data["response"],
                    "Question Difficulty": difficulties[-1],
                },
            )

        # If there are multiple processes running numpyro, it errors. So we use this mutex to prevent that.
        while cache.get(MCMC_MUTEX) is not None:
            # The second mutex checks the process holding the first mutex is related to the same user.
            if cache.get(f"{MCMC_MUTEX}_{user_id}") is not None:
                # If it is, we increment this counter of the number of questions to select and
                print("Peace out!")
                cache.incr(f"{MCMC_MUTEX}_{user_id}")
                return Response(
                    {"response": "MCMC already in progress"},
                    status=status.HTTP_200_OK,
                )
            else:
                time.sleep(0.25)
        cache.set_many({MCMC_MUTEX: True, f"{MCMC_MUTEX}_{user_id}": 1}, timeout=30)
        # Infer new knowledge state
        mcmc = MCMCInference(qb_cache_manager.q_batch.initial_knowledge_state)
        print(f"difficulties={difficulties}\nguess_probs={guess_probs}\ncorrect={correct}")
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
        num_left_to_ask = qb_cache_manager.max_num_questions - len(
            qb_cache_manager.q_batch_json["answers_given"]
        )
        # Pick new questions to ask
        if num_left_to_ask > 0:
            next_questions = select_questions(
                q_batch_cache_manager=qb_cache_manager,
                user=qb_cache_manager.user,
                session_id=request.data["session_id"],
                mcmc=mcmc,
                number_to_select=None if num_left_to_ask > 1 else 1,
            )
        else:
            next_questions = []

        # Release mutex
        cache.delete_many([MCMC_MUTEX, f"{MCMC_MUTEX}_{user_id}"])

        # Is the question_batch completed?
        concept_completed = new_ks.level > qb_cache_manager.q_batch.concept.max_difficulty_level
        num_responses = len(qb_cache_manager.q_batch_json["answers_given"])
        # print(f"Number of questions asked: {len(qb_cache_manager.q_batch_json['questions'])}")
        # print(f"Number of questions answered: {num_responses}")
        max_num_of_questions_answered = num_responses >= qb_cache_manager.max_num_questions
        # Check it's not a 'revision batch' - if it is, ignore how well they do!
        if qb_cache_manager.q_batch.is_revision_batch:
            completed = "review_completed" if max_num_of_questions_answered else ""
        else:
            print(f"new_ks.raw_leve: {new_ks.raw_level}")
            doing_poorly = num_responses >= 5 and new_ks.raw_level < -1
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
            user = User.objects.get(id=user_id)
            if not user.question_batch_finished_today():
                user.questions_streak += 1
                user.save()
            # Update stored data on the question batch
            levels_progressed = (
                new_ks.level - qb_cache_manager.q_batch.initial_knowledge_state.level
            )
            qb_cache_manager.q_batch.completed = completed
            qb_cache_manager.q_batch.levels_progressed = levels_progressed
            qb_cache_manager.q_batch.concept_completed = concept_completed
            qb_cache_manager.q_batch.time_taken_to_complete = (
                datetime.utcnow().replace(tzinfo=pytz.utc) - qb_cache_manager.q_batch.time_started
            )
            qb_cache_manager.q_batch.save()
            cache.delete(question_batch_id)  # Clear the cache
            if IS_PROD:
                mixpanel.track(
                    user_id,
                    "Completed Question Batch",
                    {
                        "concept_id": concept_id,
                        "Question Batch ID": question_batch_id,
                        "Question Response ID": question_response_id,
                        "Completion type": completed,
                        "Number of questions asked": num_responses,
                        "Levels Progressed": levels_progressed,
                        "Concept Completed": concept_completed,
                        "Time taken to complete": str(
                            qb_cache_manager.q_batch.time_taken_to_complete
                        ),
                    },
                )

        return Response(
            {
                "level": ks_model.get_display_knowledge_level(new_batch=False),
                "completed": completed,
                "next_questions": next_questions,
            },
            status=status.HTTP_200_OK,
        )


def get_training_data(q_batch_json: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Get the training data for the question batch.

    args:
        q_batch_json: The question batch json.

    Return: The training data.
    """
    responses: Dict[str, str] = q_batch_json["answers_given"]
    questions: List[Dict] = q_batch_json["questions"][: len(responses)]
    difficulties = [q["difficulty"] for q in questions]
    guess_probs = [1 / len(q["answers_order_randomised"]) for q in questions]
    correct = [q["correct_answer"] == responses[str(q["id"])] for q in questions]
    return np.array(difficulties), np.array(guess_probs), np.array(correct)
