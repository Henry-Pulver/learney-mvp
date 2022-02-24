import datetime
from typing import Any, Dict
from uuid import uuid4

from django.core.cache import cache
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer
from accounts.utils import user_data_to_user_db_object
from learney_web.settings import DT_STR
from page_visits.serializers import PageVisitSerializer

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


def get_and_update_user(request: Request) -> Dict[str, Any]:
    user_id = request.data["user_id"]
    user = cache.get(f"user-{user_id}")
    if user is None:
        user_set = User.objects.filter(id=user_id)
        # If user doesn't exist, add user!
        if user_set.exists():
            user = user_set.first()
        else:
            user_data = user_data_to_user_db_object(request.data["user_data"])
            user = User.objects.create(**user_data)
            cache.set(f"user-{user_id}", user, timeout=60 * 60 * 2)

    if user.in_questions_trial:
        # Update questions streak
        today = user.question_batch_finished_today()
        # If user did a batch yesterday, the streak hasn't been broken.
        # If they didn't, it's a new streak or 0, depending on if they did it today.
        streak = user.questions_streak if user.question_batch_finished_yesterday() else int(today)
        # If statements speed up view by not saving in the DB unless necessary
        if user.questions_streak != streak or user.utc_tz_difference != request.data[
            "user_data"
        ].get("utc_tz_difference", 0):
            user.questions_streak = streak
            user.utc_tz_difference = request.data["user_data"].get("utc_tz_difference", 0)
            user.save()
        return {"questions_streak": streak, "batch_completed_today": today}
    return {}


class PageVisitView(APIView):
    def post(self, request: Request, format=None):
        update_session(request)
        user_id = request.data.get("user_id", f"anonymous-user|{uuid4()}")
        user_data = get_and_update_user(request) if not user_id.startswith("anonymous-user") else {}
        serializer = PageVisitSerializer(
            data={
                "user_id": user_id,
                "session_id": request.session.session_key,
                "page_extension": request.data.get("page_extension"),
            }
        )
        if serializer.is_valid():
            serializer.save()
            data_output = {**serializer.data}
            data_output.update(user_data)
            return Response(data_output, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
