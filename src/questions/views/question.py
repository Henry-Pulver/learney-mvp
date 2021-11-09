import json
from random import shuffle

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models import QuestionModel, QuestionTagModel
from questions.serializers import QuestionSerializer

MAX_NUMBER_OF_QUESTIONS = 5


class QuestionView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            user_id = request.GET["user_id"]
            concept_id = request.GET["concept_id"]
            map_uuid = request.GET["map_uuid"]

            # Get all relevant questions
            all_questions = QuestionModel.objects.prefetch_related("tags").prefetch_related(
                "responses"
            )
            concept_questions = all_questions.filter(
                tags__concept_id=concept_id, tags__map__unique_id=map_uuid
            )

            unanswered_questions = concept_questions.filter(responses=None).order_by("?")
            user_responses = concept_questions.filter(responses__user_id=user_id)
            incorrectly_answered_questions = user_responses.filter(
                responses__correct=False
            ).order_by("responses__time_asked")
            correctly_answered_questions = user_responses.filter(responses__correct=True).order_by(
                "responses__time_asked"
            )

            # Select the next question set from possible options
            questions_chosen = []
            for question_entry in [
                entry
                for query_set in [
                    unanswered_questions,
                    incorrectly_answered_questions,
                    correctly_answered_questions,
                ]
                for entry in query_set
            ]:
                if question_entry not in questions_chosen:
                    questions_chosen.append(question_entry)
                if len(questions_chosen) == MAX_NUMBER_OF_QUESTIONS:
                    break

            num_mistakes_allowed = round(
                sum(1 / len(question.answer_text) for question in questions_chosen) / 2
            )
            question_serializers = [QuestionSerializer(q) for q in questions_chosen]

            response_payload = {
                "correct_threshold": len(questions_chosen) - num_mistakes_allowed,
                "question_set": [ser.data for ser in question_serializers],
            }
            return Response(response_payload, status=status.HTTP_200_OK)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None) -> Response:
        # Add question
        serializer = QuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        saved_model = serializer.save()
        # Add tags
        for tag in json.loads(request.data["tags"]):
            QuestionTagModel.objects.create(
                question_id=saved_model.id,
                map_uuid=request.data["map_uuid"],
                concept_id=tag,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
