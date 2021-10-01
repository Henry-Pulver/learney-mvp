from typing import Dict, List, Set


def get_predecessor_dict(edges: List[Dict[str, Dict[str, str]]]) -> Dict[str, Set[str]]:
    """From a list of edges as defined in the map json, outputs a dictionary mapping all
    concept_id's to sets of their dependencies.

    Args:
        edges (List[Dict[str, Dict[str, str]]]): the list of edges defined in the map json file

    Returns:
        Dict[str, Set[str]]: Dictionary of {concept_id: {set of concept_id's of dependencies of
         this concept}}
    """
    predecessor_dict: Dict[str, Set[str]] = {}
    for edge in edges:
        if edge["data"]["target"] in predecessor_dict:
            predecessor_dict[edge["data"]["target"]].add(edge["data"]["source"])
        else:
            predecessor_dict[edge["data"]["target"]] = {edge["data"]["source"]}
    return predecessor_dict


def get_concept_names(content_json: Dict[str, Dict]) -> Dict[str, str]:
    return {node["data"]["id"]: node["data"]["name"] for node in content_json["nodes"]}
