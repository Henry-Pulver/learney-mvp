from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from questions.models.question_batch import QuestionBatch
from questions.question_selection import select_questions

# from silk.profiling.profiler import silk_profile


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

            # Get all the precomputed json data from the cache
            q_batch_json = cache.get(f"question_json:{question_batch_id}")
            # And redo the computations now if it's not there!
            if q_batch_json is None:
                q_batch_json = question_batch.json()

            question = select_questions(
                concept_id=concept_id,
                question_batch_json=q_batch_json,
                user=User.objects.get(id=user_id),
                session_id=request.GET["session_id"],
                save_question_to_db=True,
                number_to_select=1,
                question_batch=question_batch,
            )[0]

            # TODO: Track with Mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
