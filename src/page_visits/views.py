from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from page_visits.serializers import PageVisitSerializer


class PageVisitView(APIView):
    # TODO: Add GET to allow frontend to know if this is a new user or not then only show intro if new!

    def post(self, request: Request, format=None):
        serializer = PageVisitSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
