from datetime import datetime

import pytz
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.inference import MCMCInference
from questions.models import QuestionResponse
from questions.question_selection import select_question
from silk.profiling.profiler import silk_profile


class QuestionResponseView(APIView):
    @silk_profile(name="Question Response - Infer Knowledge and Select new Question")
    def post(self, request: Request, format=None) -> Response:
        try:
            # Extract data from request
            concept_id = request.data["concept_id"]

            # Save the response in the DB
            q_response: QuerySet[QuestionResponse] = QuestionResponse.objects.filter(
                user=request.data["user_id"],
                question_batch=request.data["question_set"],
                correct=None,
            )
            q_response.update(
                correct=request.data["correct"],
                response=request.data["response"],
                time_to_respond=datetime.utcnow().replace(tzinfo=pytz.utc)
                - q_response[0].time_asked,
            )
            q_response = (
                QuestionResponse.objects.filter(
                    user=request.data["user_id"],
                    question_batch=request.data["question_set"],
                    correct=request.data["correct"],
                )
                .prefetch_related("user__knowledge_states__concept")
                .prefetch_related("question_batch__responses")
                .latest("time_asked")
            )
            q_response.correct = request.data["correct"]
            q_response.response = request.data["response"]
            q_response.time_to_respond = (
                datetime.utcnow().replace(tzinfo=pytz.utc) - q_response.time_asked
            )
            q_response.save()

            # Infer new knowledge state
            difficulties, guess_probs, correct = q_response.question_batch.training_data
            mcmc = MCMCInference(q_response.question_batch.initial_knowledge_state)
            mcmc.run_mcmc_inference(
                difficulties=difficulties, guess_probs=guess_probs, answers=correct
            )
            new_theta = mcmc.inferred_theta_params

            # Update inferredKnowledgeState in the DB
            prev_ks = q_response.user.knowledge_states.all().filter(
                concept__cytoscape_id=concept_id
            )
            prev_ks.update(mean=new_theta.mean, std_dev=new_theta.std_dev)
            prev_ks = prev_ks[0]

            # Check it's not a 'revision batch' - if it is, ignore how well they do!
            revision = (
                q_response.question_batch.level_at_start > prev_ks.concept.max_difficulty_level
            )
            # Is the question_batch completed?
            concept_completed = prev_ks.knowledge_level > prev_ks.concept.max_difficulty_level
            doing_poorly = len(correct) >= 5 and prev_ks.knowledge_level < -0.5
            max_num_of_questions = len(correct) >= 10
            completed = (
                "completed_concept"
                if concept_completed and not revision
                else "doing_poorly"
                if doing_poorly and not revision
                else "max_num_of_questions"
                if max_num_of_questions
                else None
            )
            response_payload = {"level": prev_ks.knowledge_level, "completed": completed}

            if completed:
                # Update stored data on the question batch
                q_response.question_batch.completed = completed
                q_response.question_batch.levels_progressed = (
                    prev_ks.knowledge_level
                    - q_response.question_batch.initial_knowledge_state.level
                )
                q_response.question_batch.concept_completed = concept_completed
                q_response.question_batch.save()
            else:
                # Pick a new question and send it back
                response_payload["next_question"] = select_question(
                    concept_id=concept_id,
                    question_batch=q_response.question_batch,
                    user=q_response.user,
                    session_id=request.data["session_id"],
                    mcmc=mcmc,
                )

            return Response(response_payload, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
