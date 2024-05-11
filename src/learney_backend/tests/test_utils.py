import datetime
from typing import Optional, Tuple

import pytest

from learney_backend.utils import (
    get_base_domain,
    get_video_id_timestart,
    is_pdf_url,
    is_youtube_url,
)

TEST_YT_URLS_CORRECT = [
    ("https://www.youtube.com/watch?v=WR9qCSXJlyY", "WR9qCSXJlyY", datetime.timedelta(seconds=0)),
    (
        "https://www.youtube.com/watch?v=0LNQxT9LvM0&t=233",
        "0LNQxT9LvM0",
        datetime.timedelta(seconds=233),
    ),
    ("https://youtu.be/WUvTyaaNkzM?t=87", "WUvTyaaNkzM", datetime.timedelta(seconds=87)),
]


@pytest.mark.parametrize("url_tuple", TEST_YT_URLS_CORRECT)
def test_is_yt_url__pass(url_tuple: Tuple[str, str, Optional[datetime.timedelta]]):
    assert is_youtube_url(url_tuple[0]) is True


TEST_YT_URLS_INCORRECT = [
    "https://www.youtube.com/watch",
    "https://www.youtube.com/watch&v=WR9qCSXJlyY",
    "https://www.youtube.com",
    "https://www.youtube.com/watch?v=0LNQxT9LvM0&t=",
    "https://www.youtube.com/watch?v=&t=233",
    "https://www.youtube.com/?v=0LNQxT9LvM0&t=233",
    "https://youtu.be",
    "https://youtu.be/watch?v=WUvTyaaNkzM&t=87",
    "https://youtu.be/WUvTyaaNkzM&t=87",
    "https://app.learney.me/maps/original_map",
]


@pytest.mark.parametrize("url", TEST_YT_URLS_INCORRECT)
def test_is_yt_url__fail(url: str):
    assert is_youtube_url(url) is False


@pytest.mark.parametrize("url,video_id,time_code", TEST_YT_URLS_CORRECT)
def test_get_video_id_timestart(url: str, video_id: str, time_code: Optional[datetime.timedelta]):
    vid_id, start = get_video_id_timestart(url)
    assert vid_id == video_id
    assert start == time_code


TEST_PDF_URLS = [
    ("https://www.davidsilver.uk/wp-content/uploads/2020/03/MDP.pdf", True),
    (
        "https://www.math.utah.edu/~zwick/Classes/Fall2012_2270/Lectures/Lecture40_with_Examples.pdf",
        True,
    ),
    ("https://www.google.com/search?q=test", False),
    ("https://www.youtube.com/watch", False),
    ("https://app.learney.me/maps/original/not_a_pdf", False),
]


@pytest.mark.parametrize("url,is_pdf", TEST_PDF_URLS)
def test_is_pdf_url(url: str, is_pdf: bool):
    assert is_pdf_url(url) == is_pdf


TEST_BASE_DOMAINS = [
    ("https://www.davidsilver.uk/wp-content/uploads/2020/03/MDP.pdf", "davidsilver.uk"),
    (
        "https://www.math.utah.edu/~zwick/Classes/Fall2012_2270/Lectures/Lecture40_with_Examples.pdf",
        "math.utah.edu",
    ),
    ("https://www.google.com/search?q=test", "google.com"),
    ("https://google.com/search?q=test", "google.com"),
    ("https://www.youtube.com/watch", "youtube.com"),
    ("https://app.learney.me/maps/original/not_a_pdf", "app.learney.me"),
    ("https://youtu.be/WUvTyaaNkzM&t=87", "youtu.be"),
]


@pytest.mark.parametrize("url,base_domain", TEST_BASE_DOMAINS)
def test_get_base_domain(url: str, base_domain: str):
    assert get_base_domain(url) == base_domain
