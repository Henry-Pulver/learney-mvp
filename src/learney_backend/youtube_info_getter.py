from typing import Dict

import requests

from learney_web.settings import YOUTUBE_API_KEY


def get_youtube_video_info(video_id: str) -> Dict:
    """Get video info from youtube.

    Args:
        video_id: The video id of the video (can be found in the url).

    Format of the response:
     {
       "kind": "youtube#video",
       "etag": "9sGsheeLpqx-um3ozFhvjGs164M",
       "id": "WR9qCSXJlyY",
       "snippet": {
         "publishedAt": "2013-02-22T01:21:52Z",
         "channelId": "UC4a-Gbdw7vOaccHmFo40b9g",
         "title": "Matrix addition and subtraction | Matrices | Precalculus | Khan Academy",
         "description": "Practice this lesson yourself on KhanAcademy.org right now: \nhttps://...",
         "thumbnails": {
           "default": {
             "url": "https://i.ytimg.com/vi/WR9qCSXJlyY/default.jpg",
             "width": 120,
             "height": 90
           },
           "medium": {<dict-same-as-above-with-h=180-w=320>},
           "high": {<dict-same-as-above-with-h=360-w=480>},
           "standard": {<dict-same-as-above-with-h=480-w=640>},
           "maxres": {<dict-same-as-above-with-h=720-w=1280>},
         },
         "channelTitle": "Khan Academy",
         "categoryId": "27",
         "liveBroadcastContent": "none",
         "defaultLanguage": "en",
         "localized": {"title": <same-as-title-above>, "description": <same-as-description-above>},
         "defaultAudioLanguage": "en"
       },
       "contentDetails": {
         "duration": "PT5M35S",
         "dimension": "2d",
         "definition": "hd",
         "caption": "true",
         "licensedContent": true,
         "contentRating": {},
         "projection": "rectangular"
       },
       "statistics": {"viewCount": "649670", "likeCount": "1485", "favoriteCount": "0", "commentCount": "62"}
     }
    """
    return (
        requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "id": video_id,
                "key": YOUTUBE_API_KEY,
                "part": "snippet,contentDetails,statistics",
            },
        )
        .json()
        .get("items", [{}])[0]
    )


def get_youtube_channel_info(channel_id: str) -> Dict:
    """Get video info from youtube.

    Args:
        channel_id: The YouTube channel id

    Format of the response:
        {
          "kind": "youtube#channel",
          "etag": "8lND7WGbX-VLufG-tNYNJ5853PA",
          "id": "UC4a-Gbdw7vOaccHmFo40b9g",
          "snippet": {
            "title": "Khan Academy",
            "description": "Khan Academy is a 501(c)(3) nonprofit organization with the mission of providing a free, ",
            "customUrl": "khanacademy",
            "publishedAt": "2006-11-17T02:12:21Z",
            "thumbnails": {
              "default": {
                "url": "https://yt3.ggpht.com/ytc/AKedOLTYTpeOiL8n_l9gepDh3m3vczvElfHZO-BR6oAf=s88-c-k-c0x00ffffff-no-rj",
                "width": 88,
                "height": 88
              },
              "medium": {<dict-same-as-above-with-h=180-w=320>},
              "high": {<dict-same-as-above-with-h=360-w=480>},
            },
            "localized": {"title": <same-as-title-above>, "description": <same-as-description-above>},
            "country": "US"
          },
          "contentDetails": {"relatedPlaylists": {"likes": "", "uploads": "UU4a-Gbdw7vOaccHmFo40b9g"},
          "statistics": {
            "viewCount": "1952655119",
            "subscriberCount": "7170000",
            "hiddenSubscriberCount": false,
            "videoCount": "8221"
          }
        }
    """
    return (
        requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={
                "id": channel_id,
                "key": YOUTUBE_API_KEY,
                "part": "snippet,contentDetails,statistics",
            },
        )
        .json()
        .get("items", [{}])[0]
    )
