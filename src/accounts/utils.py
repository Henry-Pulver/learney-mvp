from typing import Dict


def user_data_to_user_db_object(user_data: Dict) -> Dict:
    return {
        "id": user_data["sub"],
        "name": user_data.get("name", ""),
        "nickname": user_data.get("nickname", ""),
        "given_name": user_data.get("given_name", ""),
        "family_name": user_data.get("family_name", ""),
        "picture": user_data.get("picture", ""),
        "locale": user_data.get("locale", ""),
    }
