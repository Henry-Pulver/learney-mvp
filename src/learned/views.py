from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learned.models import LearnedModel
from learned.serializers import LearnedSerializer
from learney_web.settings import DT_STR, IS_PROD, mixpanel


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
        entry = LearnedModel.objects.filter(
            user_id=request.data["user_id"], map__unique_id=request.data["map"]
        ).latest("timestamp")
        new_learned_set = set(request.data["learned_concepts"])
        prev_learned_set = set(entry.learned_concepts)
        learned_added = list(new_learned_set - prev_learned_set)
        learned_removed = list(prev_learned_set - new_learned_set)

        if IS_PROD:
            # Track with mixpanel
            mixpanel.track(
                request.data["user_id"],
                "Learned",
                {
                    "Learned set": learned_added or learned_removed,
                    "Learned added or removed": "Added" if learned_added else "Removed",
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
                    "Learned set": learned_added or learned_removed,
                    "Learned added or removed": "Added" if learned_added else "Removed",
                    "Map": entry.map.name,
                    "map_uuid": request.data["map"],
                    "session_id": request.data["session_id"],
                },
            )
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
