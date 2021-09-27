import json
from typing import Dict, Union
from uuid import UUID

import requests
import yaml
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_backend.models import ContentLinkPreview, ContentVote
from learney_backend.serializers import LinkPreviewSerializer, VoteSerializer

with open("link_preview_api_key.yaml", "r") as secrets_file:
    LINK_PREVIEW_API_KEY = yaml.load(secrets_file, Loader=yaml.Loader)["API_KEY"]


class ContentLinkPreviewView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            map_uuid = UUID(request.GET["map_uuid"])
            concept = request.GET["concept"]
            url = request.GET["url"]
            print(f"Attempting to retrieve concept: {concept} from map {map_uuid}, url: {url}")
            retrieved_entry = ContentLinkPreview.objects.filter(
                map_uuid=map_uuid, concept=concept, url=url
            ).latest("preview_last_updated")
            print("Object exists in DB!")
            serializer = LinkPreviewSerializer(retrieved_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            print(f"ContentLinkPreviewView error for url {request.GET['url']}: {e}")
            preview_data = requests.get(
                "http://api.linkpreview.net",
                params={"q": request.GET["url"], "key": LINK_PREVIEW_API_KEY},
            )
            if preview_data.status_code == 200:
                link_prev_dict: Dict[str, str] = json.loads(preview_data.text)
                db_dict = {
                    "map_uuid": UUID(request.GET["map_uuid"]),
                    "description": link_prev_dict["description"],
                    "concept": request.GET["concept"],
                    "url": request.GET["url"],
                    "title": link_prev_dict["title"],
                    "image_url": link_prev_dict["image"],
                }
                print(f"Found from linkpreview.net, contents: {db_dict}")
                self._serialize_and_respond(db_dict)
                return Response(db_dict, status=status.HTTP_200_OK)
            else:
                print("Not found in linkpreview.net!")
                return Response(None, status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None) -> Response:
        return self._serialize_and_respond(request)

    @staticmethod
    def _serialize_and_respond(request: Union[Request, Dict[str, str]]) -> Response:
        data = request if isinstance(request, dict) else request.data
        serializer = LinkPreviewSerializer(data=data)
        print(f"Serializer: {serializer}")
        if serializer.is_valid():
            serializer.save()
            print(f"{serializer.data} saved in DB!")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"ContentLinkPreviewSerializer errors: {serializer.errors}")
        return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)


class ContentVoteView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            entries = ContentVote.objects.filter(
                user_id=request.GET["user_id"], map_uuid=request.GET["map_uuid"]
            )
            url_dicts = entries.values("url").distinct()
            data = {
                url_dict["url"]: entries.filter(url=url_dict["url"]).latest("vote_time").vote
                for url_dict in url_dicts
            }
            return Response(
                data, status=status.HTTP_200_OK if len(data) > 0 else status.HTTP_204_NO_CONTENT
            )
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None) -> Response:
        try:
            content_links = ContentLinkPreview.objects.filter(
                map_uuid=request.data["map_uuid"], url=request.data["url"]
            )
            data = {
                "map_uuid": UUID(request.data["map_uuid"]),
                "user_id": request.data["user_id"],
                "concept": request.data.get(
                    "concept",
                    content_links.latest("preview_last_updated").concept
                    if content_links.count() > 0
                    else "",
                ),
                "url": request.data["url"],
                "vote": request.data["vote"],
            }
            print(f"ContentVoteView request data: {data}")
            print(f"Vote type: {type(data['vote'])}")
            serializer = VoteSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
