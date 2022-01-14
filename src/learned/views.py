from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from knowledge_maps.models import KnowledgeMapModel
from learned.models import LearnedModel
from learned.serializers import LearnedSerializer
from learney_web.settings import IS_PROD, mixpanel


class LearnedView(APIView):
    def get(self, request: Request, format=None):
        try:
            entry = LearnedModel.objects.filter(
                user_id=request.GET["user_id"], map__unique_id=request.GET["map"]
            ).latest("timestamp")
            serializer = LearnedSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        serializer = LearnedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        # Find the learned concepts added or removed and whether they were added or removed
        prev_entries = LearnedModel.objects.filter(
            user_id=request.data["user_id"], map__unique_id=request.data["map"]
        )
        no_entries = prev_entries.count() == 0
        if no_entries:
            relevant_map = KnowledgeMapModel.objects.get(unique_id=request.data["map"])
        else:
            entry = prev_entries.latest("timestamp")

        new_learned_set = set(request.data["learned_concepts"])
        prev_learned_set = set([]) if no_entries else set(entry.learned_concepts)
        learned_added = list(new_learned_set - prev_learned_set)
        learned_removed = list(prev_learned_set - new_learned_set)

        mixpanel_dict = {
            "Learned set": learned_added or learned_removed,
            "Learned added or removed": "Added" if learned_added else "Removed",
            "Map URL extension": relevant_map.url_extension
            if no_entries
            else entry.map.url_extension,
            "Map Title": relevant_map.title if no_entries else entry.map.title,
            "map_uuid": request.data["map"],
            "session_id": request.data["session_id"],
        }
        # Track with mixpanel
        mixpanel.track(
            request.data["user_id"], "Learned" if IS_PROD else "Test Event", mixpanel_dict
        )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
