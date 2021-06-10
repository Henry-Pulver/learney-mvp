import os
import requests
import yaml
import json
from typing import Dict, Union

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist

from learney_backend.models import ContentLinkPreview, ContentVote
from learney_backend.serializers import LinkPreviewSerializer, VoteSerializer

with open("link_preview_api_key.yaml", "r") as secrets_file:
    LINK_PREVIEW_API_KEY = yaml.load(secrets_file, Loader=yaml.Loader)["API_KEY"]


# Render the graph
def index(request):
    return render(
        request,
        f"{os.path.dirname(os.getcwd())}/src/learney_backend/templates/learney_backend/index.html",
    )


class ContentLinkPreviewView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            concept = request.GET["concept"]
            url = request.GET["url"]
            print(f"Attempting to retrieve from DB with concept: {concept}, url: {url}")
            retrieved_entry = ContentLinkPreview.objects.get(concept=concept, url=url)
            print("Object exists in DB!")
            serializer = LinkPreviewSerializer(retrieved_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as e:
            preview_data = requests.get("http://api.linkpreview.net", params={"q": request.GET["url"], "key": LINK_PREVIEW_API_KEY})
            print(f"ContentLinkPreviewView error: {e}")
            print(f"OBJECT DOESN'T EXIST, link preview response:{preview_data.status_code}")
            if preview_data.status_code == 200:
                link_prev_dict: Dict[str, str] = json.loads(preview_data.text)
                db_dict = {"description": link_prev_dict["description"],
                           "concept": request.GET["concept"],
                           "url": request.GET["url"],
                           "title": link_prev_dict["title"],
                           "image_url": link_prev_dict["image"]}
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
        print(f"Data: {data}")
        serializer = LinkPreviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            print(f"{serializer.data} saved in DB!")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"ContentLinkPreviewSerializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentVoteView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            entries = ContentVote.objects.filter(user_id=request.GET["user_id"])
            url_dicts = entries.values("url").distinct()
            data = {url_dict["url"]: entries.filter(url=url_dict["url"]).latest("vote_time").vote for url_dict in url_dicts}
            return Response(data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as error:
            return Response(error, status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None) -> Response:
        data = {
            "user_id": request.POST["user_id"],
            "concept": request.POST.get("concept", ContentLinkPreview.objects.get(url=request.POST["url"]).concept),
            "url": request.POST["url"],
            "vote": request.POST["vote"]
        }
        print(f"ContentVoteView request data: {data}")
        serializer = VoteSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
