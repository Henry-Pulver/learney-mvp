from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User


class AuthorisedUsersView(APIView):
    def get(self, request: Request, format=None) -> Response:
        response = User.objects.filter(in_questions_trial=True).values_list("id", flat=True)
        return Response(response, status=status.HTTP_200_OK)
