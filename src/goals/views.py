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
        # Find the goal added or removed and whether it was added or removed
        entry = GoalModel.objects.filter(
            user_id=request.data["user_id"], map__unique_id=request.data["map"]
        ).latest("timestamp")
        new_goals_set = set(request.data["goal_concepts"])
        prev_goals_set = set(entry.goal_concepts)
        goal_added = new_goals_set - prev_goals_set
        goal_removed = prev_goals_set - new_goals_set

        if IS_PROD:
            # Track with mixpanel
            mixpanel.track(
                request.data["user_id"],
                "Set Goal",
                {
                    "Goal set": goal_added.pop() if goal_added else goal_removed.pop(),
                    "Goal added or removed": "Added" if goal_added else "Removed",
                    "Map": entry.map.name,
                    "map_uuid": request.data["map"],
                    "session_id": request.data["session_id"],
                },
            )
        else:
            mixpanel.track(
                request.data["user_id"],
                "Test Event",
                {
                    "Goal set": goal_added.pop() if goal_added else goal_removed.pop(),
                    "Goal added or removed": "Added" if goal_added else "Removed",
                    "Map": entry.map.name,
                    "map_uuid": request.data["map"],
                    "session_id": request.data["session_id"],
                },
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
