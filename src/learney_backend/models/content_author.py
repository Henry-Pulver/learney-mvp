from typing import Dict

from bs4 import BeautifulSoup
from django.db import models

from learney_backend.base_models import UUIDModel
from learney_backend.utils import IMG_TAGS, get_base_url, meta_content_from_name_tags, url_regex
from learney_backend.youtube_info_getter import get_youtube_channel_info


class ContentAuthor(UUIDModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, help_text="Thumbnail image of the author")
    youtube_channel_id = models.CharField(
        max_length=100, blank=True, null=True, help_text="Youtube channel ID"
    )
    retry_get_from_youtube = models.BooleanField(default=False)

    last_updated = models.DateTimeField(auto_now=True)

    def json(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
        }

    def populate_from_youtube(self) -> None:
        channel_info = get_youtube_channel_info(self.youtube_channel_id)
        if channel_info is not None:
            self.name = channel_info["snippet"]["title"]
            self.image_url = channel_info["snippet"]["thumbnails"]["high"]["url"]
        else:
            self.retry_get_from_youtube = True
        self.save()

    def populate_from_website(self, url: str, response_soup: BeautifulSoup) -> None:
        # Either get the image tag from the website or use the first <img> element on the page
        image_url_or_extension = meta_content_from_name_tags(
            response_soup, IMG_TAGS
        ) or response_soup.find("img").get("src", "")
        self.image_url = ""
        # Sometimes the img src is not absolute, so we need to prepend the url
        if url_regex(image_url_or_extension) is None:  # Check if it's a relative url
            self.image_url += get_base_url(url)
        self.image_url += image_url_or_extension

        self.save()
