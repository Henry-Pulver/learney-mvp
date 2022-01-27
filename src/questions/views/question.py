from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models import QuestionResponse
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_set import QuestionSet
from questions.question_selection import select_question
from questions.utils import get_today, uuid_and_params_from_frontend_id


class QuestionSetView(APIView):
    def get(self, request: Request, format=None) -> Response:
        concept_id = request.GET["concept_id"]
        user_id = request.GET["user_id"]
        session_id = request.GET["session_id"]
        prev_set = QuestionSet.objects.filter(completed=False, time_started__gte=get_today())
        if prev_set.exists():
            question_set = prev_set[0]
        else:
            ks = InferredKnowledgeState.objects.get(user=user_id, concept__cytoscape_id=concept_id)
            question_set = QuestionSet.objects.create(
                user=user_id,
                level_at_start=ks.knowledge_level,
                initial_knowledge_mean=ks.knowledge_state.mean,
                initial_knowledge_std_dev=ks.knowledge_state.std_dev,
                session_id=session_id,
            )

        # TODO: Track with Mixpanel

        return Response(question_set.json(), status=status.HTTP_200_OK)


class QuestionView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            concept_id = request.GET["concept_id"]
            user_id = request.GET["user_id"]
            question_set = QuestionSet.objects.get(id=request.GET["question_set"]).selected_related(
                "responses"
            )

            knowledge_state = InferredKnowledgeState.objects.get(
                user=user_id, concept__cytoscape_id=concept_id
            ).select_related("user")

            question = select_question(concept_id, question_set, knowledge_state)
            chosen_template_id, sampled_params = uuid_and_params_from_frontend_id(question["id"])

            # Track the question was sent in the DB
            QuestionResponse.objects.create(
                user=user_id,
                question_template=chosen_template_id,
                question_params=sampled_params,
                question_set=question_set,
                session_id=request.GET["session_id"],
                time_to_respond=None,
            )

            # TODO: Track with Mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
