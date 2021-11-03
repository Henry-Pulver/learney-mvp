from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from questions.serializers import QuestionResponseSerializer


class QuestionResponseView(APIView):
    def post(self, request: Request, format=None) -> Response:
        serializer = QuestionResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
