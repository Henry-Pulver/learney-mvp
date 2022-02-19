from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    def get(self, request: Request, format=None) -> Response:
        return Response("Success!", status=status.HTTP_200_OK)
