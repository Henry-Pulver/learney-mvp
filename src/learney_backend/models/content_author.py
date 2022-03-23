from typing import Dict

from bs4.element import Tag
from django.db import models

from learney_backend.base_models import UUIDModel
from learney_backend.utils import IMG_TAGS, meta_content_from_name_tags
from learney_backend.youtube_info_getter import get_youtube_channel_info


class ContentAuthor(UUIDModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, help_text="Thumbnail image of the author")
    youtube_channel_id = models.CharField(
        max_length=100, blank=True, null=True, help_text="Youtube channel ID"
    )

    last_updated = models.DateTimeField(auto_now=True)

    def json(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "picture_url": self.image_url,
        }

    def populate_from_youtube(self) -> None:
        channel_info = get_youtube_channel_info(self.youtube_channel_id)
        self.name = channel_info["snippet"]["title"]
        self.image_url = channel_info["snippet"]["thumbnails"]["high"]["url"]
        self.save()

    def populate_from_website(self, response_soup: Tag) -> None:
        # Either get the image tag from the website or use the first <img> element on the page
        self.image_url = (
            meta_content_from_name_tags(response_soup, IMG_TAGS) or response_soup.find("img")["src"]
        )
        self.save()
