import json
from typing import Dict

import requests

from learney_web.settings import LINK_PREVIEW_API_KEY


def get_from_linkpreview_net(request_dict: Dict[str, str]) -> Dict[str, str]:
    preview_data = requests.get(
        "http://api.linkpreview.net",
        params={"q": request_dict["url"], "key": LINK_PREVIEW_API_KEY},
    )
    db_dict = {
        "map": request_dict["map"],
        "concept": request_dict["concept"],
        "concept_id": request_dict["concept_id"],
        "url": request_dict["url"],
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
    return db_dict
