from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_web.settings import IS_PROD, mixpanel
from questions.models import QuestionResponse
from questions.models.inferred_knowledge_state import InferredKnowledgeState
from questions.models.question_batch import QuestionBatch
from questions.question_batch_cache_manager import QuestionBatchCacheManager
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
                initial_display_knowledge_level=ks.get_display_knowledge_level(new_batch=True),
                session_id=session_id,
            )
        cache.set(question_batch.id, question_batch, 600)

        qb_cache_manager = QuestionBatchCacheManager(question_batch.id)
        question_batch_json = qb_cache_manager.q_batch_json

        if IS_PROD:
            mixpanel.track(
                user_id,
                "Question Batch Started",
                {
                    "concept_id": concept_id,
                    "Question Batch ID": str(question_batch.id),
                    "Initial Knowledge Level Mean": question_batch.initial_knowledge_mean,
                    "Initial Knowledge Level Variance": question_batch.initial_knowledge_std_dev,
                    "Initial Display Knowledge Level": question_batch.initial_display_knowledge_level,
                    "session_id": session_id,
                },
            )

        # Select another question if most recent one is answered
        print(
            f"Batch. Answers given: {len(question_batch_json['answers_given'])}. Questions asked: {len(question_batch_json['questions'])}"
        )
        if (
            len(question_batch_json["answers_given"]) >= len(question_batch_json["questions"]) - 1
            and len(question_batch_json["questions"]) < question_batch_json["max_num_questions"]
        ):
            select_questions(
                q_batch_cache_manager=qb_cache_manager,
                user=ks.user,
                session_id=session_id,
                save_question_to_db=True,
                number_to_select=min(
                    2
                    - (
                        len(question_batch_json["questions"])
                        - len(question_batch_json["answers_given"])
                    ),
                    question_batch_json["max_num_questions"]
                    - len(question_batch_json["questions"]),
                ),
                num_qs_answered_on_concept=QuestionResponse.objects.filter(
                    user=user_id, question_template__concept=ks.concept
                )
                .exclude(response=None)
                .count(),
            )

        print(
            f"Knowledge state: ({round(ks.knowledge_state.mean, 2)}, {round(ks.knowledge_state.std_dev, 2)}),\t"
            f"Display knowledge level {question_batch.initial_display_knowledge_level},\t"
            f"Max reached: {ks.highest_level_achieved}"
        )
        print(f"Num questions chosen: {len(question_batch_json['questions'])}")
        print(f"Num answers given: {len(question_batch_json['answers_given'])}")
        answers_dict = question_batch_json["answers_given"]
        question_batch_json["answers_given"] = [
            answers_dict[str(q["id"])]
            for q in question_batch_json["questions"]
            if answers_dict.get(str(q["id"]))
        ]
        return Response(question_batch_json, status=status.HTTP_200_OK)
