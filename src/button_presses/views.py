import datetime

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_web.settings import DT_STR, IS_PROD, mixpanel


class ButtonPressView(APIView):
    def post(self, request: Request, format=None) -> Response:
        button_press_info = {
            "Current URL": request.data["Current URL"],
            "Button Name": request.data["Button Name"],
        }
        if IS_PROD:
            mixpanel.track(
                request.data["user_id"],
                "Button Press",
                button_press_info,
            )
            return Response("Success! Sent to mixpanel", status=status.HTTP_200_OK)
        else:
            mixpanel.track(
                request.data["user_id"],
                "Test Event",
                button_press_info,
            )
        return Response(
            f"Success! Not sent to mixpanel because this isn't a production deployment.\n"
            f"JSON sent: {[request.data['user_id'], button_press_info]}",
            status=status.HTTP_200_OK,
        )


class MapEventTrackingView(APIView):
    def post(self, request: Request, format=None) -> Response:
        user_id = request.data.pop("user_id")
        event_type = request.data.pop("Event Type")
        if IS_PROD:
            mixpanel.track(
                user_id,
                event_type,
                request.data,
            )
            return Response("Success! Sent to mixpanel", status=status.HTTP_200_OK)
        return Response(
            f"Success! Not sent to mixpanel because this isn't a production deployment.\n"
            f"JSON sent: {[user_id, event_type, request.data]}",
            status=status.HTTP_200_OK,
        )
