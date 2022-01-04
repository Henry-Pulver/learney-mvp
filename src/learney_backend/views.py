import datetime
import json
from typing import Dict, Union
from uuid import UUID

import requests
import yaml
from django.utils.datastructures import MultiValueDictKeyError
from pytz import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_backend.models import ContentLinkPreview, ContentVote
from learney_backend.serializers import LinkPreviewSerializer, VoteSerializer
from learney_web.settings import DT_STR, IS_PROD, mixpanel

UTC = timezone("UTC")

with open("link_preview_api_key.yaml", "r") as secrets_file:
    LINK_PREVIEW_API_KEY = yaml.load(secrets_file, Loader=yaml.Loader)["API_KEY"]


class ContentLinkPreviewView(APIView):
    def get(self, request: Request, format=None) -> Response:
        try:
            retrieved_entries = ContentLinkPreview.objects.filter(
                map__unique_id=request.GET["map"],
                concept=request.GET["concept"],
                url=request.GET["url"],
            )
            if retrieved_entries.count() == 0:
                return self.get_from_linkpreview_net(request)
            else:
                retrieved_entry = retrieved_entries.latest("preview_last_updated")

                # If no details found and old, try linkpreview.net
                utc_now = UTC.localize(datetime.datetime.utcnow())
                if retrieved_entry.description == "" and (
                    utc_now - retrieved_entry.preview_last_updated > datetime.timedelta(weeks=1)
                ):
                    return self.get_from_linkpreview_net(request)
                else:
                    serializer = LinkPreviewSerializer(
                        retrieved_entry, context={"request": request}
                    )
                    # if serializer.is_valid():
                    return Response(serializer.data, status=status.HTTP_200_OK)
                    # else:
                    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None) -> Response:
        return self._serialize_and_respond(request)

    @staticmethod
    def _serialize_and_respond(request: Union[Request, Dict[str, str]]) -> Response:
        data = request if isinstance(request, dict) else request.data
        serializer = LinkPreviewSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            print(f"{serializer.data} saved in DB!")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(f"ContentLinkPreviewSerializer errors: {serializer.errors}")
        return Response(str(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def get_from_linkpreview_net(self, request):
        preview_data = requests.get(
            "http://api.linkpreview.net",
            params={"q": request.GET["url"], "key": LINK_PREVIEW_API_KEY},
        )
        db_dict = {
            "map": UUID(request.GET["map"]),
            "concept": request.GET["concept"],
            "concept_id": request.GET["concept_id"],
            "url": request.GET["url"],
        }
        if preview_data.status_code == 200:
            link_prev_dict: Dict[str, str] = json.loads(preview_data.text)
            db_dict.update(
                {
                    "description": link_prev_dict["description"],
                    "title": link_prev_dict["title"],
                    "image_url": link_prev_dict["image"],
                }
            )
            print(f"Found from linkpreview.net, contents: {db_dict}")
        else:
            print("Not found in linkpreview.net!")
            db_dict.update({"description": "", "title": "", "image_url": ""})
        return self._serialize_and_respond(db_dict)


class TotalVoteCountView(APIView):
    def get(self, request: Request, format=None) -> Response:
        """Get the overall +/- vote count for each item of content."""
        entries = ContentVote.objects.filter(map__unique_id=request.GET["map"]).exclude(vote=None)
        # Below logic: for each url, find the most recent vote from each user who voted on
        #  that url and add them, with False -> -1 and True -> +1
        # TODO: Doesn't account for not-voted-on urls - left to frontend to deal with
        data = {
            url_dict["url"]: sum(
                2 * int(v_entry["vote"]) - 1  # True, False or None
                for v_entry in entries.filter(url=url_dict["url"]).values("vote")
            )
            for url_dict in entries.values("url").distinct()
        }

        return Response(data, status=status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT)


class ContentVoteView(APIView):
    def get(self, request: Request, format=None) -> Response:
        """Get votes for an individual user."""
        try:
            entries = ContentVote.objects.filter(
                user_id=request.GET["user_id"], map__unique_id=request.GET["map"]
            )
            url_dicts = entries.values("url").distinct()
            data = {
                url_dict["url"]: entries.filter(url=url_dict["url"]).latest("timestamp").vote
                for url_dict in url_dicts
            }
            return Response(data, status=status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT)
        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None) -> Response:
        try:
            request.session["last_action"] = datetime.datetime.utcnow().strftime(DT_STR)
            content_links = ContentLinkPreview.objects.filter(
                map__unique_id=request.data["map"], url=request.data["url"]
            )
            data = {
                "map": request.data["map"],
                "session_id": request.data.get("session_id"),
                "user_id": request.data.get("user_id"),
                "concept": request.data.get(
                    "concept",
                    content_links.latest("preview_last_updated").concept
                    if content_links.count() > 0
                    else "",
                ),
                "url": request.data.get("url"),
                "vote": request.data.get("vote"),
            }
            serializer = VoteSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                if IS_PROD:
                    mixpanel.track(
                        data["user_id"],
                        "Vote",
                        {
                            "url": data["url"],
                            "vote_direction": data["vote"],
                            "concept": data["concept"],
                            "map_uuid": data["map"],
                            "session_id": data["session_id"],
                        },
                    )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
