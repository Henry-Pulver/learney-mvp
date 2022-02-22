from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import GoalModel
from knowledge_maps.models import KnowledgeMapModel
from learney_web.settings import IS_PROD, mixpanel


class GoalView(APIView):
    def get(self, request: Request, format=None):
        try:
            user_id = request.GET["user_id"]
            map_uuid = request.GET["map"]
            goal = GoalModel.get(user_id, map_uuid)
            if goal is None:
                return Response(str("No goal found"), status=status.HTTP_204_NO_CONTENT)
            return Response(goal.json(), status=status.HTTP_200_OK)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        map_uuid = request.data.pop("map")
        request.data["map"] = KnowledgeMapModel.objects.get(unique_id=map_uuid)
        goal_model = GoalModel(**request.data)

        # Find the goal added or removed and whether it was added or removed
        prev_entry = GoalModel.get(goal_model.user_id, map_uuid)

        # Work out the difference between the previously set goals and new goals
        new_goals_set = set(request.data["goal_concepts"])
        prev_goals_set = set(prev_entry.goal_concepts) if prev_entry is not None else set([])

        goal_added = new_goals_set - prev_goals_set
        goal_removed = prev_goals_set - new_goals_set

        mixpanel_dict = {
            "Goal set": goal_added.pop() if goal_added else goal_removed.pop(),
            "Goal added or removed": "Added" if goal_added else "Removed",
            "Map URL extension": request.data["map"].url_extension,
            "Map Title": request.data["map"].title,
            "map_uuid": map_uuid,
            "session_id": request.data["session_id"],
        }

        goal_model.save()
        # Track with mixpanel
        mixpanel.track(
            request.data["user_id"], "Set Goal" if IS_PROD else "Test Event", mixpanel_dict
        )
        return Response(goal_model.json(), status=status.HTTP_201_CREATED)
