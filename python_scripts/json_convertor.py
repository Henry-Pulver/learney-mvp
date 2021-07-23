import csv
import json
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
from typing import Dict, List

import matplotlib.cm as cm
import numpy as np

JSON_GRAPH_DICT = Dict[str, List[Dict[str, Dict[str, str]]]]


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


def convert_tsv_to_json(tsv_path: Path, show_subjects: bool = False) -> JSON_GRAPH_DICT:
    """Converts a .tsv into a dictionary of the form that can be consumed by cytoscape.js as a.

    .json.

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

    with open(tsv_path, newline="") as tsvfile:
        file = csv.reader(tsvfile, delimiter="\t", quotechar="|")

        nodes, edges, subjects, sources = [], [], set(), []
        for i, row in enumerate(file):
            if i == 0:
                continue

            # CONVERT THE DEPENDENCIES TO A LIST
            dependencies = row[2].replace(" ", "").split(",")

            node_id = str(row[0])
            subjects.add(str(row[3]))
            nodes.append(
                {
                    "data": {
                        "id": node_id,
                        "name": str(row[1]),
                        "lectures": str(row[4]),
                        "description": str(row[5]),
                        "urls": row[6].replace(" ", "").split(","),
                        "nodetype": "concept",
                        "relative_importance": 1,
                    },
                    "classes": "concept",
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
                        "classes": "subject",
                    },
                )

    for source_id, num_targets in Counter(sources).items():
        for node in nodes:
            if node["data"]["id"] == source_id:
                node["data"]["relative_importance"] = max(1, 0.7 * (num_targets + 1) ** 0.5)
                continue

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
