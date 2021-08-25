from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from goals.serializers import GoalSerializer


class GoalView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = GoalModel.objects.filter(
                user_id=request.GET["user_id"], map_uuid=request.GET["map_uuid"]
            ).latest("last_updated")
            serializer = GoalSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None):
        serializer = GoalSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
