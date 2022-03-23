import datetime

from django.core.cache import cache
from django.utils.datastructures import MultiValueDictKeyError
from pytz import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from learney_backend.models import ContentLinkPreview, ContentVote
from learney_backend.serializers import VoteSerializer
from learney_web.settings import IS_PROD, mixpanel

UTC = timezone("UTC")


class ContentLinkPreviewView(APIView):
    def get(self, request: Request, format=None) -> Response:
        url = request.GET["url"]
        link_preview: ContentLinkPreview = cache.get(url)
        if link_preview is None:
            # TODO: requires links are unique in the db given a map and concept!
            #  write a migration to ensure this is true!
            link_preview, created = ContentLinkPreview.objects.get_or_create(
                map__unique_id=request.GET["map"],
                concept=request.GET["concept"],
                concept_id=request.GET["concept_id"],
                url=url,
            )
            cache.set(url, link_preview, timeout=60 * 60 * 24 * 7)

            if created:
                link_preview.populate()

        checked = link_preview.checked_by.all().filter(id=request.GET["user_id"]).exists()

        utc_now = UTC.localize(datetime.datetime.utcnow())
        if link_preview.description == "" and (
            utc_now - link_preview.preview_last_updated > datetime.timedelta(weeks=1)
        ):
            link_preview.populate()

        return Response({**link_preview.json(), "checked": checked}, status=status.HTTP_200_OK)


class TotalVoteCountView(APIView):
    def get(self, request: Request, format=None) -> Response:
        """Get the overall +/- vote count for each item of content."""
        # TODO: Doesn't account for not-voted-on urls - left to frontend to deal with
        data = cache.get(f"total_votes:{request.GET['map']}")
        if data is None:
            # Below logic: for each url, find the most recent vote from each user who voted on
            #  that url and add them, with False -> -1 and True -> +1
            entries = ContentVote.objects.filter(map__unique_id=request.GET["map"]).exclude(
                vote=None
            )
            data = {
                url_dict: sum(
                    2 * int(vote) - 1  # True, False or None
                    for vote in entries.filter(url=url_dict).values_list("vote", flat=True)
                )
                for url_dict in entries.values_list("url", flat=True).distinct()
            }
            cache.set(f"total_votes:{request.GET['map']}", data, timeout=60 * 60 * 24)

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
            return Response(
                data,
                status=status.HTTP_200_OK if data else status.HTTP_204_NO_CONTENT,
            )

        except MultiValueDictKeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request, format=None) -> Response:
        try:
            all_map_content_links = ContentLinkPreview.objects.filter(
                map__unique_id=request.data["map"]
            )
            content_links = all_map_content_links.filter(url=request.data["url"])
            content_link_exists = content_links.count() > 0
            data = {
                "map": request.data["map"],
                "session_id": request.data.get("session_id"),
                "user_id": request.data.get("user_id"),
                "concept": request.data.get(
                    "concept",
                    content_links.latest("preview_last_updated").concept
                    if content_link_exists
                    else "",
                ),
                "content_link_preview": content_links.latest("preview_last_updated").pk
                if content_link_exists
                else None,
                "url": request.data.get("url"),
                "vote": request.data["vote"],
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
                            "Map URL extension": all_map_content_links[0].map.url_extension,
                            "Map Title": all_map_content_links[0].map.title,
                            "map_uuid": data["map"],
                            "session_id": data["session_id"],
                        },
                    )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as error:
            return Response(str(error), status=status.HTTP_400_BAD_REQUEST)
