from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from goals.serializers import GoalSerializer
from knowledge_maps.models import KnowledgeMapModel
from learney_web.settings import IS_PROD, mixpanel


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
        prev_entries = GoalModel.objects.filter(
            user_id=request.data["user_id"], map=request.data["map"]
        )
        no_entries = prev_entries.count() == 0
        if no_entries:
            relevant_map = KnowledgeMapModel.objects.get(unique_id=request.data["map"])
        else:
            entry = prev_entries.latest("timestamp")

        # Work out the difference between the previously set goals and new goals
        new_goals_set = set(request.data["goal_concepts"])
        prev_goals_set = set([]) if no_entries else set(entry.goal_concepts)

        goal_added = new_goals_set - prev_goals_set
        goal_removed = prev_goals_set - new_goals_set

        mixpanel_dict = {
            "Goal set": goal_added.pop() if goal_added else goal_removed.pop(),
            "Goal added or removed": "Added" if goal_added else "Removed",
            "Map URL extension": relevant_map.url_extension
            if no_entries
            else entry.map.url_extension,
            "Map Title": relevant_map.title if no_entries else entry.map.title,
            "map_uuid": request.data["map"],
            "session_id": request.data["session_id"],
        }

        # Track with mixpanel
        mixpanel.track(
            request.data["user_id"], "Set Goal" if IS_PROD else "Test Event", mixpanel_dict
        )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
