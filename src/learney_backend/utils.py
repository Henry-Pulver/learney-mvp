import json
import re
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from learney_web.settings import LINK_PREVIEW_API_KEY

# HTML Meta tag names
IMG_TAGS = ["image", "og:image", "twitter:image", "twitter:image:src"]
TITLE_TAGS = ["title", "og:title", "twitter:title"]
DESCRIPTION_TAGS = ["description", "og:description", "twitter:description"]


def get_from_linkpreview_net(url: str) -> Dict[str, str]:
    req_params = {"q": url, "key": LINK_PREVIEW_API_KEY}
    preview_data = requests.get("http://api.linkpreview.net", params=req_params)
    db_dict = {"url": url}
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
    return db_dict


def get_bs_content(element: Optional[BeautifulSoup]) -> Optional[str]:
    """Gets BeautifulSoup content if it's an element."""
    return element["content"] if element is not None else None


def meta_content_from_name_tags(soup: BeautifulSoup, name_tags: List[str]) -> Optional[str]:
    """Gets the content of the first meta tag with the given name."""
    possible_content = [get_bs_content(soup.find("meta", attrs={"name": tag})) for tag in name_tags]
    return next(filter(None, possible_content), None)


def youtube_regex(url: str) -> Optional[re.Match]:
    """Returns a regex match object if the url is a youtube url."""
    return re.match(
        "^https?://((www\.youtube\.com/watch\?v=([^&]+)(&t=(\d+))?)|(youtu\.be/(\w+)(\?t=(\d+))?))$",
        url,
    )


def get_video_id_timestart(url: str) -> Tuple[str, timedelta]:
    """Returns the video id and the start time of the video."""
    yt_regex = youtube_regex(url)
    assert yt_regex is not None
    video_id = yt_regex.group(3) or yt_regex.group(7)
    time_start = int(yt_regex.group(5) or yt_regex.group(9) or 0)
    return video_id, timedelta(seconds=time_start)


def is_youtube_url(url: str) -> bool:
    return youtube_regex(url) is not None


def is_pdf_url(url: str) -> bool:
    return re.match("^https?://(www\.)?\S+\.pdf$", url) is not None


def get_base_domain(url: str) -> str:
    """Returns the base domain of the url."""
    regex = re.match("^https?://(www\.)?([\w.]+)", url)
    if regex is None:
        return ""
    return regex.group(2)
