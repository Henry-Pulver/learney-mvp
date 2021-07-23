from typing import Dict, Set


def get_predecessor_dict(content_json: Dict[str, Dict]) -> Dict[str, Set[str]]:
    predecessor_dict: Dict[str, Set] = {}
    for edge in content_json["edges"]:
        if edge["data"]["target"] in predecessor_dict:
            predecessor_dict[edge["data"]["target"]].add(edge["data"]["source"])
        else:
            predecessor_dict[edge["data"]["target"]] = {edge["data"]["source"]}
    return predecessor_dict


def get_concept_names(content_json: Dict[str, Dict]) -> Dict[str, str]:
    return {node["data"]["id"]: node["data"]["name"] for node in content_json["nodes"]}
