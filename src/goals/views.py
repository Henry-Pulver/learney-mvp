import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from goals.serializers import GoalSerializer
from learney_web.settings import DT_STR


class GoalView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = GoalModel.objects.filter(
                user_id=request.GET["user_id"], map_uuid=request.GET["map_uuid"]
            ).latest("timestamp")
            serializer = GoalSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        serializer = GoalSerializer(
            data={
                "map_uuid": request.data.get("map_uuid", None),
                "user_id": request.data.get("user_id", None),
                "session_id": request.session.session_key,
                "goal_concepts": request.data.get("goal_concepts", None),
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
