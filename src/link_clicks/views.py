from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_backend.models import ContentLinkPreview
from learney_web.settings import DT_STR, IS_PROD, mixpanel
from link_clicks.serializers import LinkClickSerializer


class LinkClickView(APIView):
    def post(self, request: Request, format=None):
        try:
            url = request.data.get("url", None)
            map = UUID(request.data["map"]) if "map" in request.data else None
            concept_id = request.data.get("concept_id", None)
            retrieved_entry = ContentLinkPreview.objects.filter(
                map__unique_id=map, concept_id=concept_id, url=url
            ).latest("preview_last_updated")
            data = {
                "map": map,
                "user_id": request.data.get("user_id", None),
                "session_id": request.data.get("session_id", None),
                "content_link_preview": retrieved_entry.pk,
                "concept_id": concept_id,
                "url": url,
            }
            serializer = LinkClickSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                if IS_PROD:
                    mixpanel.track(
                        data["user_id"],
                        "Content Link Click",
                        {
                            "url": data["url"],
                            "map_uuid": str(data["map"]),
                            "concept_id": concept_id,
                            "concept_name": retrieved_entry.concept,
                            "content_link_preview_id": retrieved_entry.pk,
                            "content_link_preview_name": retrieved_entry.title,
                            "session_id": data["session_id"],
                        },
                    )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
