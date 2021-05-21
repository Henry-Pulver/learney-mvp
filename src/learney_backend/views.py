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
from django.http.request import QueryDict

from learney_backend.models import ContentLinkPreview
from learney_backend.serializers import LinkPreviewSerializer, VoteSerializer

with open("link_preview_api_key.yaml", "r") as secrets_file:
    LINK_PREVIEW_API_KEY = yaml.load(secrets_file, Loader=yaml.Loader)["API_KEY"]
    print(LINK_PREVIEW_API_KEY)


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
            print(f"Error: {e}")
            print(f"OBJECT DOESN'T EXIST, link preview response:{preview_data.status_code}")
            if preview_data.status_code == 200:
                link_prev_dict: Dict[str, str] = json.loads(preview_data.text)
                db_dict = {"description": link_prev_dict["description"],
                           "concept": request.GET["concept"],
                           "url": request.GET["url"],
                           "title": link_prev_dict["title"],
                           "image_url": link_prev_dict["image"]}
                print(f"Found from linkpreview.net, type: {type(db_dict)}, contents: {db_dict}")
                self._serialize_and_respond(db_dict)
                return Response(db_dict, status=status.HTTP_200_OK)
            else:
                print("Not found in linkpreview.net!")
                return Response(preview_data.content, status=status.HTTP_204_NO_CONTENT)

    def post(self, request: Request, format=None) -> Response:
        return self._serialize_and_respond(request)

    def _serialize_and_respond(self, request: Union[Request, Dict[str, str]]):
        data = request if isinstance(request, dict) else request.data
        # data = request
        print(f"Data: {data}")
        serializer = LinkPreviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            print(f"{serializer.data} saved in DB!")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"THIS IS FUCKED. Errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentVoteView(APIView):
    def post(self, request: Request, format=None) -> Response:
        serializer = VoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
