from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

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
            completed="",
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
            ks.update_std_dev()
            question_batch = QuestionBatch.objects.create(
                user=ks.user,
                concept=ks.concept,
                initial_knowledge_mean=ks.knowledge_state.mean,
                initial_knowledge_std_dev=ks.knowledge_state.std_dev,
                initial_display_knowledge_level=0,
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
            select_questions(
                concept_id=concept_id,
                question_batch_json=question_batch_json,
                question_batch=question_batch,
                session_id=session_id,
                user=ks.user,
                save_question_to_db=True,
                number_to_select=2,
            )
            print(f"Num questions chosen: {len(question_batch_json['questions'])}")
            cache.set(f"question_json:{question_batch.id}", question_batch_json, 1200)

        return Response(question_batch_json, status=status.HTTP_200_OK)
