import datetime
from uuid import UUID, uuid4

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_web.settings import DT_STR
from link_clicks.serializers import LinkClickSerializer


class LinkClickView(APIView):
    def post(self, request: Request, format=None):
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        data = {
            "map_uuid": UUID(request.data["map_uuid"]),
            "user_id": request.data["user_id"],
            "session_id": request.session.session_key,
            "url": request.data["url"],
        }
        serializer = LinkClickSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
