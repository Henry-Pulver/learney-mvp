import datetime

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_web.settings import DT_STR
from page_visits.serializers import PageVisitSerializer


class PageVisitView(APIView):
    # TODO: Add GET to allow frontend to know if this is a new user or not then only show intro if new!

    def post(self, request: Request, format=None):
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        serializer = PageVisitSerializer(
            data={
                "user_id": request.data["user_id"],
                "session_id": request.session.session_key,
                "page_extension": request.data["page_extension"],
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
