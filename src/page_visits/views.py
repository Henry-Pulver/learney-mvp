import datetime
from uuid import uuid4

from django.http import HttpRequest
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_web.settings import DT_STR
from page_visits.serializers import PageVisitSerializer

ORIG_MAP_NAME = "original_map"

SESSION_KEY_CYCLE_TIME = 3600  # secs
SESSION_EXPIRY_TIME = 4 * 7 * 24 * 60 * 60  # 4 weeks in seconds


def cycle_session_key_if_old(request: Request) -> None:
    now = datetime.datetime.utcnow()
    last_action_time = datetime.datetime.strptime(
        request.session.get("last_action", now.strftime(DT_STR)), DT_STR
    )
    time_since_last_action = now - last_action_time
    if time_since_last_action.total_seconds() > SESSION_KEY_CYCLE_TIME:
        request.session.cycle_key()


def update_session(request: Request) -> None:
    cycle_session_key_if_old(request)
    if request.session.session_key is None:
        request.session.cycle_key()
    request.session.set_expiry(SESSION_EXPIRY_TIME)


def get_or_generate_user_id(request: Request) -> str:
    if request.data.get("user_id") is not None:
        return request.data["user_id"]
    else:
        return f"anonymous-user|{uuid4()}"


class PageVisitView(APIView):
    # TODO: Add GET to allow frontend to know if this is a new user or not then only show intro if new!

    def post(self, request: Request, format=None):
        update_session(request)
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        serializer = PageVisitSerializer(
            data={
                "user_id": get_or_generate_user_id(request),
                "session_id": request.session.session_key,
                "page_extension": request.data.get("page_extension"),
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
