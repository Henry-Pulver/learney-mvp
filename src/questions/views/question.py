from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch
from questions.question_selection import select_question
from questions.utils import get_today
from silk.profiling.profiler import silk_profile


class QuestionBatchView(APIView):
    @silk_profile(name="Get Question Batch")
    def get(self, request: Request, format=None) -> Response:
        # Extract payload from request
        concept_id = request.GET["concept_id"]
        user_id = request.GET["user_id"]
        session_id = request.GET["session_id"]

        # If a previous batch of questions exists, use that. Otherwise make a new one
        prev_batch = QuestionBatch.objects.filter(
            user=user_id,
            completed=False,
            time_started__gte=get_today(),
            concept__cytoscape_id=concept_id,
        )
        ks = (
            InferredKnowledgeState.objects.select_related("concept")
            .select_related("user")
            .get(user=user_id, concept__cytoscape_id=concept_id)
        )
        if prev_batch.exists():
            question_batch: QuestionBatch = prev_batch[0]
        else:
            question_batch = QuestionBatch.objects.create(
                user=ks.user,
                concept=ks.concept,
                level_at_start=ks.knowledge_level,
                initial_knowledge_mean=ks.knowledge_state.mean,
                initial_knowledge_std_dev=ks.knowledge_state.std_dev,
                session_id=session_id,
            )

        # TODO: Track with Mixpanel

        question_batch_json = question_batch.json()

        if len(question_batch_json["questions"]) == 0:
            question_batch_json["questions"].append(
                select_question(
                    concept_id=concept_id,
                    question_batch=question_batch,
                    session_id=session_id,
                    user=ks.user,
                )
            )

        return Response(question_batch_json, status=status.HTTP_200_OK)


class QuestionView(APIView):
    """Currently not being used!"""

    def get(self, request: Request, format=None) -> Response:
        try:
            concept_id = request.GET["concept_id"]
            user_id = request.GET["user_id"]
            question_batch: QuestionBatch = QuestionBatch.objects.get(
                id=request.GET["question_set"]
            ).selected_related("responses")

            knowledge_state: InferredKnowledgeState = InferredKnowledgeState.objects.select_related(
                "user"
            ).get(user=user_id, concept__cytoscape_id=concept_id)

            question = select_question(
                concept_id=concept_id,
                question_batch=question_batch,
                user=knowledge_state.user,
                session_id=request.GET["session_id"],
            )

            # TODO: Track with Mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
