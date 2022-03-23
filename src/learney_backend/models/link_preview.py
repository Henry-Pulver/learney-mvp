import warnings
from io import BytesIO
from typing import Dict

import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.db import models

import isodate
from knowledge_maps.models import KnowledgeMapModel
from learney_backend.models.content_author import ContentAuthor
from learney_backend.models.content_tag import ContentTag
from learney_backend.read_time import get_pdf_info, get_read_time
from learney_backend.utils import (
    DESCRIPTION_TAGS,
    IMG_TAGS,
    TITLE_TAGS,
    get_base_domain,
    get_from_linkpreview_net,
    get_video_id_timestart,
    is_pdf_url,
    is_youtube_url,
    meta_content_from_name_tags,
)
from learney_backend.youtube_info_getter import get_youtube_video_info
from learney_web.validators import validate_numeric


class PopulateException(Exception):
    pass


class ContentLinkPreview(models.Model):
    map = models.ForeignKey(
        KnowledgeMapModel,
        on_delete=models.CASCADE,
        related_name="link_previews",
        help_text="Map this content link corresponds to",
    )
    concept = models.TextField(help_text="Name of the concept the link corresponds to")
    concept_id = models.CharField(
        max_length=8,
        validators=[validate_numeric],
        help_text="ID of the concept the link corresponds to (defined in the map json)",
        null=True,  # Remove once all null fields are removed from DB's!
    )
    url = models.URLField(max_length=2048, help_text="The resource URL")

    title = models.TextField(
        blank=True,
        help_text="Title of the link preview - shows as the title of the item of content",
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the link preview - shows below the title of the content",
    )
    image_url = models.URLField(
        blank=True, null=True, help_text="Thumbnail image of the link preview"
    )
    content_type = models.CharField(
        null=True,
        default=None,
        help_text="Type of content on the link",
        max_length=20,
        choices=[
            ("video", "Video"),
            ("article", "Article"),
            ("lecture_slides", "Lecture Slides"),
            ("image", "Image"),
            ("pdf", "PDF"),
            ("website", "Website"),
            ("code", "Code"),
            ("github", "GitHub"),
            ("playground", "Playground"),
            ("other", "Other"),
        ],
    )
    estimated_time_to_complete = models.DurationField(
        null=True,
        blank=True,
        default=None,
        help_text="Estimated time to complete the content on the link",
    )
    author = models.ForeignKey(
        ContentAuthor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Author of the content on the link",
    )
    tags = models.ManyToManyField(
        ContentTag, help_text="Tags associated with the content on the link"
    )

    preview_last_updated = models.DateTimeField(auto_now=True)

    def json(self) -> Dict:
        json_response = {
            "map": self.map,
            "concept": self.concept,
            "concept_id": self.concept_id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "image_url": self.image_url,
            "content_type": self.content_type,
            "estimated_time_to_complete": self.estimated_time_to_complete.value_to_string(
                "estimated_time_to_complete"
            ),
            "author": self.author.json() if self.author else None,
            "tags": [tag.json() for tag in self.tags.all()],
        }
        cache.set(self.url, json_response, 60 * 60 * 24)
        return json_response

    def populate(self):
        try:
            if is_youtube_url(self.url):
                self.populate_from_youtube()
            elif is_pdf_url(self.url):
                self.populate_from_pdf()
            else:
                self.populate_from_website()
        except PopulateException as e:
            warnings.warn(f"Failed to populate link preview for {self.url}: {e}")
        self.save()

    def populate_from_youtube(self) -> None:
        video_id, time_start = get_video_id_timestart(self.url)
        yt_info = get_youtube_video_info(video_id)

        self.title = yt_info["snippet"]["title"]
        self.description = yt_info["snippet"]["description"]
        self.image_url = yt_info["snippet"]["thumbnails"]["high"]["url"]
        self.content_type = "video"
        full_duration = isodate.parse_duration(yt_info["contentDetails"]["duration"])
        self.estimated_time_to_complete = full_duration - time_start

        self.author, created = ContentAuthor.objects.get_or_create(
            youtube_channel_id=yt_info["snippet"]["channelId"]
        )
        if created:
            self.author.populate_from_youtube()

    def populate_from_pdf(self) -> None:
        pdf_response = requests.get(self.url)

        self.content_type = "pdf"
        pdf_info = get_pdf_info(BytesIO(pdf_response.content))
        self.estimated_time_to_complete = pdf_info["read_time"]

        # Get a link preview image from linkpreview.net
        # TODO: replace with a screenshot of the first page of the PDF
        linkpreview_info = get_from_linkpreview_net(self.url)
        self.title = pdf_info["title"] or linkpreview_info["title"]
        self.description = pdf_info["description"] or linkpreview_info["description"]
        self.image_url = linkpreview_info["image_url"]

        # Set author
        base_url = get_base_domain(self.url)
        base_url_response = requests.get(base_url)
        base_soup = BeautifulSoup(base_url_response.content, "html.parser")
        author_name = (
            pdf_info["author"]
            or meta_content_from_name_tags(base_soup, ["og:site_name"])
            or base_url
        )
        self.author, created = ContentAuthor.objects.get_or_create(name=author_name)
        if created:
            self.author.populate_from_website(base_soup)

    def populate_from_website(self) -> None:
        response = requests.get(self.url)
        if response.status_code != 200:
            raise PopulateException(f"Got {response.status_code} response from {self.url}")
        soup = BeautifulSoup(response.content, "html.parser")

        self.title = soup.title.string or meta_content_from_name_tags(soup, TITLE_TAGS)
        self.description = meta_content_from_name_tags(soup, DESCRIPTION_TAGS)
        self.image_url = meta_content_from_name_tags(soup, IMG_TAGS)
        self.content_type = "website"
        self.estimated_time_to_complete = get_read_time(soup.get_text())
        base_domain = get_base_domain(self.url)

        # Sort out the author!
        if base_domain in ["medium.com", "towardsdatascience.com"]:
            # Get author name from meta tags
            author_name = meta_content_from_name_tags(soup, ["author"])
            self.author = ContentAuthor.objects.get_or_create(name=author_name)[0]

            # "Oorf oorf!" walrus operator below :=
            if author_url := meta_content_from_name_tags(soup, ["article:author"]):
                author_response: requests.Response = requests.get(author_url)
                author_soup = BeautifulSoup(author_response.content, "html.parser")
                self.author.populate_from_website(author_soup)
        else:
            # Otherwise, we'll use the base website name as the author name!
            base_domain_response = requests.get(f"https://{base_domain}")
            if base_domain_response.status_code != 200:
                base_soup = BeautifulSoup(base_domain_response.content, "html.parser")
                self.author = ContentAuthor.objects.get_or_create(
                    name=base_soup.title.string
                    or meta_content_from_name_tags(base_soup, TITLE_TAGS),
                    picture_url=meta_content_from_name_tags(base_soup, IMG_TAGS),
                )[0]
            else:
                # Worst case scenario we use the base web domain as the author name!
                self.author = ContentAuthor.objects.get_or_create(name=base_domain)[0]
