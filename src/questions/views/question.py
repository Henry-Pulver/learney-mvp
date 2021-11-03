import json

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.models import QuestionConceptTagModel
from questions.serializers import QuestionResponseSerializer


class QuestionView(APIView):
    def get(self, request: Request, format=None) -> Response:
        # Get the next question

        # Get all possible questions

        # Pick based on current knowledge state & past questions seen

        raise NotImplementedError

    def post(self, request: Request, format=None) -> Response:
        # Add question
        serializer = QuestionResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        saved_model = serializer.save()
        # Add tags
        for tag in json.loads(request.data["tags"]):
            QuestionConceptTagModel.objects.create(
                question_id=saved_model.id,
                map_uuid=request.data["map_uuid"],
                concept_id=tag,
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)
