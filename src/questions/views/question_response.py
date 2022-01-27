from datetime import datetime

import pytz
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.inference import MCMCInference
from questions.models import QuestionResponse
from questions.question_selection import select_question


class QuestionResponseView(APIView):
    def post(self, request: Request, format=None) -> Response:
        # Extract data from request
        concept_id = request.data["concept_id"]

        # Save the response in the DB
        q_response = (
            QuestionResponse.objects.filter(
                user=request.data["user_id"],
                question_set=request.data["question_set"],
                correct=None,
            )
            .latest("time_asked")
            .prefetch_related("user__knowledge_states__concept")
            .prefetch_related("question_set__responses")
        )
        q_response.update(
            correct=request.data["correct"],
            response=request.data["response"],
            time_to_respond=datetime.utcnow().replace(tzinfo=pytz.utc) - q_response.timestamp,
        )

        # Infer new knowledge state
        guess_probs, difficulties, correct = q_response.question_set.training_data
        mcmc = MCMCInference(q_response.initial_knowledge_state)
        mcmc.run_mcmc_inference(difficulties, guess_probs, correct)
        new_theta = mcmc.inferred_theta_params

        # Update inferredKnowledgeState in the DB
        prev_ks = q_response.user.knowledge_states.all().get(concept=concept_id)
        prev_ks.update(mean=new_theta.mean, std_dev=new_theta.std_dev)

        # Is the question_set completed?
        concept_completed = prev_ks.knowledge_level > prev_ks.concept.max_difficulty_level
        doing_poorly = len(correct) >= 5 and prev_ks.knowledge_level < -0.5
        max_num_of_questions = len(correct) >= 10
        completed = (
            "completed_concept"
            if concept_completed
            else "doing_poorly"
            if doing_poorly
            else "max_num_of_questions"
            if max_num_of_questions
            else None
        )
        response_payload = {"level": prev_ks.knowledge_level, "completed": completed}

        if completed:
            # Update stored data on the question set
            q_response.question_set.update(
                completed=completed,
                levels_progressed=prev_ks.knowledge_level - q_response.initial_knowledge_state,
                concept_completed=concept_completed,
            )
        else:
            # Pick a new question and send it back
            response_payload["next_question"] = select_question(
                concept_id=concept_id,
                question_set=q_response.question_set,
                user=q_response.user,
                mcmc=mcmc,
            )

        return Response(response_payload, status=status.HTTP_200_OK)
