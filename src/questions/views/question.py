from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from questions.question_batch_cache_manager import QuestionBatchCacheManager
from questions.question_selection import select_questions

# from silk.profiling.profiler import silk_profile


class QuestionView(APIView):
    # @silk_profile(name="Get Question")
    def get(self, request: Request, format=None) -> Response:
        try:
            user_id = request.GET["user_id"]
            question_batch_id = request.GET["question_set"]

            qb_cache_manager = QuestionBatchCacheManager(question_batch_id)

            question = select_questions(
                q_batch_cache_manager=qb_cache_manager,
                user=User.objects.get(id=user_id),
                session_id=request.GET["session_id"],
                save_question_to_db=True,
                number_to_select=1,
            )[0]

            # TODO: Track with mixpanel

            return Response(question, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
