from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch
from questions.question_selection import select_questions
from questions.utils import get_today

# from silk.profiling.profiler import silk_profile


class QuestionBatchView(APIView):
    # @silk_profile(name="Get Question Batch")
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
        ks = cache.get(f"InferredKnowledgeState:concept:{concept_id}user:{user_id}")
        if ks is None:
            ks = (
                InferredKnowledgeState.objects.select_related("concept")
                .select_related("user")
                .get(user=user_id, concept__cytoscape_id=concept_id)
            )
        if prev_batch.exists():
            print("PREV BATCH")
            question_batch: QuestionBatch = prev_batch[0]
        else:
            print("NEW BATCH")
            question_batch = QuestionBatch.objects.create(
                user=ks.user,
                concept=ks.concept,
                initial_knowledge_mean=ks.knowledge_state.mean,
                initial_knowledge_std_dev=ks.knowledge_state.std_dev,
                session_id=session_id,
            )
        cache.set(question_batch.id, question_batch, 600)

        # TODO: Track with Mixpanel

        question_batch_json = question_batch.json()

        # Select another question if most recent one is answered
        if (
            len(question_batch_json["answers_given"]) == 0
            or question_batch_json["answers_given"][-1]
        ):
            question_batch_json["questions"] += select_questions(
                concept_id=concept_id,
                question_batch=question_batch,
                session_id=session_id,
                user=ks.user,
                save_question_to_db=True,
                number_to_select=2,
            )

        return Response(question_batch_json, status=status.HTTP_200_OK)


class QuestionView(APIView):
    # @silk_profile(name="Get Question")
    def get(self, request: Request, format=None) -> Response:
        try:
            concept_id = request.GET["concept_id"]
            user_id = request.GET["user_id"]
            question_batch_id = request.GET["question_set"]

            question_batch: QuestionBatch = cache.get(question_batch_id)
            if question_batch is None:
                question_batch = QuestionBatch.objects.prefetch_related("responses").get(
                    id=question_batch_id
                )

            question = select_questions(
                concept_id=concept_id,
                question_batch=question_batch,
                user=User.objects.get(id=user_id),
                session_id=request.GET["session_id"],
                save_question_to_db=True,
                number_to_select=1,
            )[0]

            # TODO: Track with Mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
