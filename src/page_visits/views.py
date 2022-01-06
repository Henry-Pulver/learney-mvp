from uuid import uuid4

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from page_visits.serializers import PageVisitSerializer


def get_or_generate_user_id(request: Request) -> str:
    if request.data.get("user_id") is not None:
        return request.data["user_id"]
    else:
        return f"anonymous-user|{uuid4()}"


class PageVisitView(APIView):
    # TODO: Add GET to allow frontend to know if this is a new user or not then only show intro if new!

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
