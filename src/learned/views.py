from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learned.models import LearnedModel
from learned.serializers import LearnedSerializer


class LearnedView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = LearnedModel.objects.filter(user_id=request.GET["user_id"]).latest(
                "last_updated"
            )
            serializer = LearnedSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(error, status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None):
        serializer = LearnedSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
