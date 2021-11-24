import datetime

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
                user_id=request.GET["user_id"], map_uuid=request.GET["map_uuid"]
            ).latest("timestamp")
            serializer = LearnedSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(str(error), status=status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None):
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        serializer = LearnedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        if IS_PROD:
            mixpanel.track(
                request.data["user_id"],
                "Learned",
                {
                    "learned_state": request.data["learned_concepts"],
                    "map_uuid": request.data["map_uuid"],
                    "session_id": request.data["session_id"],
                },
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
