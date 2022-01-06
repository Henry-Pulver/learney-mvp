import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from goals.serializers import GoalSerializer
from learney_web.settings import DT_STR, IS_PROD, mixpanel


class GoalView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = GoalModel.objects.filter(
                user_id=request.GET["user_id"], map__unique_id=request.GET["map"]
            ).latest("timestamp")
            serializer = GoalSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        serializer = GoalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        if IS_PROD:
            mixpanel.track(
                request.data["user_id"],
                "Set Goal",
                {
                    "goal_state": request.data["goal_concepts"],
                    "map_uuid": request.data["map"],
                    "session_id": request.data["session_id"],
                },
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
