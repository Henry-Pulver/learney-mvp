import datetime
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_backend.models import ContentLinkPreview
from learney_web.settings import DT_STR
from link_clicks.serializers import LinkClickSerializer


class LinkClickView(APIView):
    def post(self, request: Request, format=None):
        try:
            request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
            url = request.data.get("url", None)
            map_uuid = UUID(request.data["map_uuid"]) if "map_uuid" in request.data else None
            concept_id = request.data.get("concept_id", None)
            retrieved_entry = ContentLinkPreview.objects.filter(
                map_uuid=map_uuid, concept_id=concept_id, url=url
            ).latest("preview_last_updated")
            data = {
                "map_uuid": map_uuid,
                "user_id": request.data.get("user_id", None),
                "session_id": request.session.session_key,
                "content_link_preview_id": retrieved_entry.pk,
                "concept_id": concept_id,
                "url": url,
            }
            print(data)
            serializer = LinkClickSerializer(data=data)
            print(serializer)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
