import datetime

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from button_presses.serializers import ButtonPressSerializer
from learney_web.settings import DT_STR


class ButtonPressView(APIView):
    def post(self, request: Request, format=None) -> Response:
        request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
        serializer = ButtonPressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
