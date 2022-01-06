from typing import Dict


def user_data_to_user_db_object(user_data: Dict) -> Dict:
    return {
        "id": user_data["sub"],
        "name": user_data["name"],
        "nickname": user_data["nickname"],
        "given_name": user_data["given_name"],
        "family_name": user_data["family_name"],
        "picture": user_data["picture"],
        "locale": user_data["locale"],
    }
