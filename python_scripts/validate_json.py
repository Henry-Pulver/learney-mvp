import json

with open("assets/content_graph.json", "r") as content_file:
    content_json = json.load(content_file)

ids = [element["data"]["id"] for element in content_json["nodes"]]

for edge in content_json["edges"]:
    assert isinstance(edge["data"]["source"], str)
    assert isinstance(edge["data"]["target"], str)
    assert edge["data"]["source"].isnumeric()
    assert edge["data"]["target"].isnumeric()
    assert edge["data"]["source"] in ids
    assert edge["data"]["target"] in ids
