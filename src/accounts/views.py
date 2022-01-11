from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from learney_backend.models import ContentLinkPreview
from learney_web.settings import IS_PROD, mixpanel


class AddCheckedView(APIView):
    def post(self, request: Request, format=None) -> Response:
        try:
            user = User.objects.get(id=request.data["user_id"])
            checked_content = ContentLinkPreview.objects.filter(
                map=request.data["map"],
                concept_id=request.data["concept_id"],
                url=request.data["url"],
            ).latest("preview_last_updated")
            if checked_content in user.checked_content_links.all():
                user.checked_content_links.remove(checked_content)
                action_name = "Uncheck Content Link"
            else:
                user.checked_content_links.add(checked_content)
                action_name = "Check Off Content Link"
            mixpanel_dict = {
                "url": request.data["url"],
                "Map URL extension": checked_content.map.url_extension,
                "Map Title": checked_content.map.title,
                "map_uuid": request.data["map"],
                "concept_name": checked_content.concept,
                "concept_id": checked_content.concept_id,
                "content_link_preview_id": checked_content.pk,
                "content_link_preview_name": checked_content.title,
            }
            if IS_PROD:
                mixpanel.track(
                    request.data["user_id"],
                    action_name,
                    mixpanel_dict,
                )
                return Response(f"{action_name}: {mixpanel_dict}", status=status.HTTP_201_CREATED)
            else:
                return Response(
                    f"Success! Not sent to mixpanel because this isn't a production deployment.\n"
                    f"JSON sent: {[request.data['user_id'], mixpanel_dict]}",
                    status=status.HTTP_200_OK,
                )
        except KeyError as e:
            return Response(f"Invalid request: {str(e)}\n\n{e}", status=status.HTTP_400_BAD_REQUEST)
