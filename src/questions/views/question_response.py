from datetime import datetime

import pytz
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.inference import GaussianParams, MCMCInference
from questions.models import QuestionResponse
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch
from questions.question_selection import select_question

# from silk.profiling.profiler import silk_profile


class QuestionResponseView(APIView):
    # @silk_profile(name="Question Response - Infer Knowledge and Select new Question")
    def post(self, request: Request, format=None) -> Response:
        # try:
        # Extract data from request
        concept_id = request.data["concept_id"]
        user_id = request.data["user_id"]

        # Save the response in the DB
        q_response: QuestionResponse = cache.get(request.data["question_response_id"])
        if q_response is None:
            q_response = QuestionResponse.objects.get(
                id=request.data["question_response_id"],
            )
        q_response.correct = request.data["correct"]
        q_response.response = request.data["response"]
        q_response.time_to_respond = (
            datetime.utcnow().replace(tzinfo=pytz.utc) - q_response.time_asked
        )
        q_response.save()

        q_batch: QuestionBatch = (
            QuestionBatch.objects.prefetch_related("user__knowledge_states__concept")
            .prefetch_related("responses__question_template__concept")
            .get(id=request.data["question_set"])
        )

        # Infer new knowledge state
        difficulties, guess_probs, correct = q_batch.training_data
        mcmc = MCMCInference(q_batch.initial_knowledge_state)
        mcmc.run_mcmc_inference(difficulties=difficulties, guess_probs=guess_probs, answers=correct)
        new_theta = mcmc.inferred_theta_params

        # Update inferredKnowledgeState in the DB
        prev_ks: QuerySet[InferredKnowledgeState] = cache.get(
            f"inferredKnowledgeState_{user_id}_{concept_id}"
        )
        if prev_ks is None:
            prev_ks = q_batch.user.knowledge_states.all().filter(concept__cytoscape_id=concept_id)
        new_ks = GaussianParams(mean=new_theta.mean, std_dev=new_theta.std_dev)
        prev_ks.update(
            mean=new_theta.mean,
            std_dev=new_theta.std_dev,
            highest_level_achieved=max(prev_ks[0].highest_level_achieved, new_ks.level),
        )
        cache.set(f"inferredKnowledgeState_{user_id}_{concept_id}", prev_ks)

        # Is the question_batch completed?
        concept_completed = new_ks.level > q_batch.concept.max_difficulty_level
        doing_poorly = len(correct) >= 5 and new_ks.level < -0.5
        max_num_of_questions_answered = len(correct) >= q_batch.max_number_of_questions
        # Check it's not a 'revision batch' - if it is, ignore how well they do!
        completed = (
            "completed_concept"
            if concept_completed and not q_batch.is_revision_batch
            else "doing_poorly"
            if doing_poorly and not q_batch.is_revision_batch
            else "max_num_of_questions"
            if max_num_of_questions_answered
            else ""
        )
        response_payload = {"level": new_ks.level, "completed": completed}

        if completed:
            # Update stored data on the question batch
            q_batch.completed = completed
            q_batch.levels_progressed = new_ks.level - q_batch.initial_knowledge_state.level
            q_batch.concept_completed = concept_completed
            q_batch.save()
        else:
            # Pick a new question and send it back
            response_payload["next_question"] = select_question(
                concept_id=concept_id,
                question_batch=q_batch,
                user=q_batch.user,
                session_id=request.data["session_id"],
                mcmc=mcmc,
            )

        return Response(response_payload, status=status.HTTP_200_OK)
        # except Exception as e:
        #     return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
