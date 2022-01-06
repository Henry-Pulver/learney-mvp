from uuid import uuid4

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer
from accounts.utils import user_data_to_user_db_object
from page_visits.serializers import PageVisitSerializer


def get_or_generate_user_id(request: Request) -> str:
    if request.data.get("user_id") is None:
        return f"anonymous-user|{uuid4()}"
    user_id = request.data["user_id"]
    # If user doesn't exist, add user!
    if User.objects.filter(id=user_id).count() == 0:
        serializer = UserSerializer(data=user_data_to_user_db_object(request.data["user_data"]))
        if serializer.is_valid():
            serializer.save()
    return user_id


class PageVisitView(APIView):
    def post(self, request: Request, format=None):
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
