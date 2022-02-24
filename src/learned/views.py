from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from knowledge_maps.models import KnowledgeMapModel
from learned.models import LearnedModel
from learney_web.settings import IS_PROD, mixpanel


class LearnedView(APIView):
    def get(self, request: Request, format=None):
        try:
            user_id = request.query_params["user_id"]
            map_uuid = request.query_params["map"]
            learned = LearnedModel.get(user_id, map_uuid)
            if learned is None:
                return Response(str("No learned found"), status=status.HTTP_204_NO_CONTENT)
            return Response(learned.json(), status=status.HTTP_200_OK)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        map_uuid = request.data.pop("map")
        request.data["map"] = KnowledgeMapModel.objects.get(unique_id=map_uuid)
        learned_model = LearnedModel(**request.data)

        # Find the learned concepts added or removed and whether they were added or removed
        prev_entry = LearnedModel.get(request.data["user_id"], map_uuid)

        new_learned_set = set(request.data["learned_concepts"])
        prev_learned_set = set(prev_entry.learned_concepts) if prev_entry is not None else set([])
        learned_added = list(new_learned_set - prev_learned_set)
        learned_removed = list(prev_learned_set - new_learned_set)

        mixpanel_dict = {
            "Learned set": learned_added or learned_removed,
            "Learned added or removed": "Added" if learned_added else "Removed",
            "Map URL extension": request.data["map"].url_extension,
            "Map Title": request.data["map"].title,
            "map_uuid": map_uuid,
            "session_id": request.data["session_id"],
        }
        # Saving the model low down the function so we don't mess up the prev_entries query
        learned_model.save()
        # Track with mixpanel
        mixpanel.track(
            request.data["user_id"], "Learned" if IS_PROD else "Test Event", mixpanel_dict
        )
        return Response(learned_model.json(), status=status.HTTP_201_CREATED)
