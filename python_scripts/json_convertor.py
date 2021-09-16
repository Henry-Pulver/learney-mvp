import csv
import json
from argparse import ArgumentParser
from collections import Counter
from copy import copy
from pathlib import Path
from typing import Any, Dict, List, Set, Union
from warnings import warn

import matplotlib.cm as cm
import numpy as np

import validators
from learney_web.utils import get_predecessor_dict

JSON_GRAPH_DICT = Dict[str, List[Dict[str, Dict[str, str]]]]


class ContentError(Exception):
    pass


def subject_to_id(subject: str) -> str:
    return subject.replace(" ", "_")


def get_colours(num_colours: int) -> List:
    colour_tuples = [cm.rainbow(x) for x in np.arange(0, 1, (1 / (num_colours - 1)) - 1e-8)]

    def col2byte(colour: float) -> int:
        """Convert a colour float to a byte integer."""
        return int(np.round(colour * 255))

    return [
        "#{:02x}{:02x}{:02x}".format(col2byte(col[0]), col2byte(col[1]), col2byte(col[3]))
        for col in colour_tuples
    ]


def remove_edge(source: str, target: str, edges: List[Dict[str, Dict[str, str]]]) -> None:
    print(f"Removing edge connecting {source} -> {target}")
    for edge in edges:
        if edge["data"]["source"] == source and edge["data"]["target"] == target:
            edges.remove(edge)
            break


def remove_unnecessary_edges(edges: List[Dict[str, Dict[str, str]]]) -> None:
    """Remove edges whose dependency structures are already covered by existing edges.

    e.g.     If X -> Y -> Z and X -> Z, then X -> Z can be cut as this dependency is already implied
    with X -> Y -> Z.
    """
    predecessor_dict = get_predecessor_dict(edges)
    for node, direct_predecessors in predecessor_dict.items():
        # check the predecessors don't overlap
        for predecessor in direct_predecessors:
            second_layer_predecessors = predecessor_dict.get(predecessor, set())
            [
                remove_edge(second_layer_pred, node, edges)  # type: ignore
                for second_layer_pred in second_layer_predecessors
                if second_layer_pred in direct_predecessors
            ]


def assert_edges_valid(edges: List[Dict[str, Dict[str, str]]]) -> List[Dict[str, Dict[str, str]]]:
    """Assert there are no loops in the tree & remove repeated."""
    error_list = []

    predecessor_dict = get_predecessor_dict(edges)
    for node, direct_predecessors in predecessor_dict.items():
        for predecessor in direct_predecessors:
            second_layer_predecessors = predecessor_dict.get(predecessor, set())
            if not all(
                [second_layer_pred != node for second_layer_pred in second_layer_predecessors]
            ):
                error_list.append(
                    f"Two nodes have each other as dependencies! {node} <-> {predecessor}"
                )

        # check for longer loops
        predecessor_set = copy(direct_predecessors)
        prev_predecessor_set: Set[str] = set()
        while len(prev_predecessor_set) != len(predecessor_set):
            prev_predecessor_set = copy(predecessor_set)
            [
                predecessor_set.union(predecessor_dict.get(predecessor, set()))
                for predecessor in prev_predecessor_set
            ]
        if node in predecessor_set:
            error_list.append(f"Found a dependency loop including node: {node}!")

    if len(set([str(edge) for edge in edges])) != len(edges):
        repeated_edges = []
        for edge in edges:
            repetition_count = edges.count(edge)
            if repetition_count > 1:
                # Remove repeated edges
                repeated_edges.append(edge)
                warn(
                    f"Edge from {edge['data']['source']} -> {edge['data']['target']} repeated {repetition_count} times!"
                )
        for edge_index_to_remove in range(1, len(repeated_edges), 2):
            edges.remove(repeated_edges[edge_index_to_remove])

    if len(error_list) > 0:
        raise ContentError(str(error_list))

    return edges


def process_urls(url_string: str) -> List[str]:
    """Converts string of comma-separated urls to list of url strings."""
    output_url_list = []
    for potential_url in url_string.replace(" ", "").split(","):
        if validators.url(potential_url):
            output_url_list.append(potential_url)
        else:
            output_url_list[-1] += potential_url
    return output_url_list


def validate_url_list(url_list: List[str]) -> None:
    for url in url_list:
        if not validators.url(url):
            raise ValueError(f"Not a valid URL: {url}")


def convert_tsv_to_json(tsv_path: Path, show_subjects: bool = False) -> JSON_GRAPH_DICT:
    """Converts a .tsv into a dictionary of the form that can be consumed by cytoscape.js as a.json.

    Args:
        tsv_path: path to .tsv file to convert
        show_subjects: whether to add subject data to the json

    Returns:
        Dictionary from tsv that can be dumped into a json to be visualised
    """
    assert (
        tsv_path.is_file() and tsv_path.exists()
    ), f"Path given ({tsv_path}) doesn't point to a valid file!"
    assert tsv_path.suffix == ".tsv", f"Path given ({tsv_path}) doesn't point to a `.tsv` file!"

    subject_missing_errors = []
    with open(tsv_path, newline="") as tsvfile:
        file = csv.reader(tsvfile, delimiter="\t", quotechar="|")

        nodes: List[Dict[str, Dict[str, Any]]] = []
        edges, subjects, sources = [], set(), []
        for i, row in enumerate(file):
            if i == 0 or len(str(row[1])) == 0:
                continue

            # Ensure it's a regulation-length row
            row = [row[i] if i < len(row) else "" for i in range(9)]

            # Convert dependencies to a list
            dependencies = row[2].replace(" ", "").split(",")

            node_id = str(row[0])
            subjects.add(str(row[3]))

            if row[3] == "":
                subject_missing_errors.append(
                    f"{row[1]} (ID={node_id}, index={i}) is missing its subject! Row in full: {row}"
                )

            nodes.append(
                {
                    "data": {
                        "id": node_id,
                        "name": str(row[1]),
                        "lectures": str(row[4]),
                        "description": str(row[5]),
                        "urls": process_urls(row[6]),
                        "nodetype": "concept",
                        "relative_importance": 1,
                    },
                }
            )
            if show_subjects:
                nodes[-1]["data"].update({"parent": subject_to_id(row[3])})

            for dependency in dependencies:
                if dependency == "":
                    continue
                source_id = str(int(dependency))
                sources.append(source_id)

                edges.append(
                    {
                        "data": {
                            "id": f"{source_id}_{node_id}",
                            "source": source_id,
                            "target": node_id,
                        }
                    }
                )
        # Add parent nodes
        if show_subjects:
            for subject, colour in zip(subjects, get_colours(len(subjects))):
                nodes.insert(
                    0,
                    {
                        "data": {
                            "id": subject_to_id(subject),
                            "name": subject,
                            "colour": colour,
                            "nodetype": "field",
                        },
                    },
                )

    for source_id, num_targets in Counter(sources).items():
        for node in nodes:
            if node["data"]["id"] == source_id:
                node["data"]["relative_importance"] = max(1, 0.7 * (num_targets + 1) ** 0.5)
                continue

    remove_unnecessary_edges(edges)
    edges = assert_edges_valid(edges)

    if len(subject_missing_errors) > 0:
        raise ContentError(str(subject_missing_errors))

    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    parser = ArgumentParser("Convert a .tsv to a .json for visualisation by cytoscape.js")
    parser.add_argument("-t", "--tsv", type=str, required=True, help=".tsv file to convert")
    parser.add_argument(
        "-j",
        "--json",
        type=str,
        default="knowledge_graph.json",
        help=".json filename to save output to",
    )
    parser.add_argument(
        "-s",
        "--show_subjects",
        action="store_true",
        help="whether to show subjects or not",
    )
    args = parser.parse_args()

    json_save_path = Path(args.json)
    json_save_path.parent.mkdir(exist_ok=True, parents=True)
    with json_save_path.open("w") as json_save_file:
        json.dump(convert_tsv_to_json(Path(args.tsv), args.show_subjects), json_save_file)
        print(f"Successfully saved to {json_save_path}")
