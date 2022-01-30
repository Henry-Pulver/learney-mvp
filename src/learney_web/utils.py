from copy import copy
from pathlib import Path
from typing import Dict, List, Set

import boto3

S3_CACHE_DIR = Path("S3_cache_dir")


def get_prerequisite_dict(
    content_json: Dict[str, List[Dict[str, Dict[str, str]]]]
) -> Dict[str, Set[str]]:
    """From the map json, output a dictionary mapping all concept_id's to sets of their
    dependencies.

    Args:
        content_json (Dict[str, List[Dict[str, Dict[str, str]]]]): the list of edges defined in the map json file

    Returns:
        Dict[str, Set[str]]: Dictionary of {concept_id: {set of concept_id's of dependencies of
         this concept}}
    """
    predecessor_dict: Dict[str, Set[str]] = {
        node["data"]["id"]: set()
        for node in content_json["nodes"]
        if node["data"]["nodetype"] == "concept"
    }
    for edge in content_json["edges"]:
        predecessor_dict[edge["data"]["target"]].add(edge["data"]["source"])
    for concept, prereqs in predecessor_dict.items():
        prereqs_to_check = copy(prereqs)
        while prereqs_to_check:
            for prereq in prereqs_to_check:
                predecessor_dict[concept] = predecessor_dict[concept].union(
                    predecessor_dict[prereq]
                )
            prereqs_to_check = prereqs_to_check.difference(predecessor_dict[concept])

    return predecessor_dict


def get_concept_names(content_json: Dict[str, Dict]) -> Dict[str, str]:
    return {node["data"]["id"]: node["data"]["name"] for node in content_json["nodes"]}


def retrieve_map_from_s3(
    s3_bucket_name: str,
    s3_key: str,
    aws_credentials: Dict[str, str],
) -> bytes:
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=aws_credentials["ACCESS_ID"],
        aws_secret_access_key=aws_credentials["SECRET_KEY"],
    )
    response = s3.Object(s3_bucket_name, s3_key).get()
    return response["Body"].read()
