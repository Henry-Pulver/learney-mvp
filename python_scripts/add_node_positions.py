import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List

JSON_GRAPH_DICT = Dict[str, List[Dict[str, Dict[str, str]]]]


def convert_tsv_to_json(graph_json_path: Path, node_position_path: Path) -> JSON_GRAPH_DICT:
    """Add the positions from one .json to a knowledge graph .json that can be consumed by
    cytoscape.js.

    Args:
        graph_json_path: path to .json file to add positions to
        node_position_path: json of node positions

    Returns:
        Dictionary that can be dumped into a json to be visualised in cytoscape.js
    """
    for json_path in [graph_json_path, node_position_path]:
        assert (
            json_path.is_file() and json_path.exists()
        ), f"Path given ({json_path}) doesn't point to a valid file!"
        assert (
            json_path.suffix == ".json"
        ), f"Path given ({json_path}) doesn't point to a `.tsv` file!"

    with graph_json_path.open("r") as graph_json_file:
        graph_dict = json.load(graph_json_file)
    with node_position_path.open("r") as node_position_file:
        node_positions = json.load(node_position_file)

    for node_id, position in node_positions.items():
        for node in graph_dict["nodes"]:
            if node["data"]["id"] == node_id:
                node.update({"position": position})
                continue

    return graph_dict


if __name__ == "__main__":
    parser = ArgumentParser("Convert a .tsv to a .json for visualisation by cytoscape.js")
    parser.add_argument(
        "-g",
        "--graph_json_path",
        type=str,
        default="assets/knowledge_graph.json",
        help=".json file to add positions to",
    )
    parser.add_argument(
        "-p",
        "--node_position_path",
        type=str,
        default="assets/NodePositions.json",
        help=".json file containing node positions",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        default="positions_knowledge_graph_v009.json",
        help=".json filename to save output to",
    )
    args = parser.parse_args()

    json_save_path = Path(args.output_path)
    json_save_path.parent.mkdir(exist_ok=True, parents=True)
    with json_save_path.open("w") as json_save_file:
        json.dump(
            convert_tsv_to_json(Path(args.graph_json_path), Path(args.node_position_path)),
            json_save_file,
        )
        print(f"Successfully saved to {json_save_path}")
