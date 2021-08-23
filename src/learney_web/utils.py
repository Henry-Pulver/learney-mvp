from typing import Dict, List, Set


def get_predecessor_dict(edges: List[Dict[str, Dict[str, str]]]) -> Dict[str, Set[str]]:
    predecessor_dict: Dict[str, Set] = {}
    for edge in edges:
        if edge["data"]["target"] in predecessor_dict:
            predecessor_dict[edge["data"]["target"]].add(edge["data"]["source"])
        else:
            predecessor_dict[edge["data"]["target"]] = {edge["data"]["source"]}
    return predecessor_dict


def get_concept_names(content_json: Dict[str, Dict]) -> Dict[str, str]:
    return {node["data"]["id"]: node["data"]["name"] for node in content_json["nodes"]}
