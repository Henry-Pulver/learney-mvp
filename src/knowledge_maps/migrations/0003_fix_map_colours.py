import json

from django.db import migrations

import boto3
from colormap import hex2rgb, hls2rgb, rgb2hex, rgb2hls
from learney_web.settings import AWS_CREDENTIALS

COLOUR_MAP = {
    "#d6dfff": "#001975",
    "#85ffff": "#006161",
    "#33ddff": "#00404d",
    "#3381ff": "#001d4d",
    "#850aff": "#210042",
    "#ff85ff": "#610061",
}
REVERTED_COLOUR_MAP = {value: key for key, value in COLOUR_MAP.items()}


def darken_hex(hex_colour: str, factor: float) -> str:
    rgb = hex2rgb(hex_colour)
    hls = rgb2hls(*rgb, False)
    hls_list = [*hls]
    hls_list[1] = max(min(hls[1] * factor, 1.0), 0.0)
    rgb = hls2rgb(*hls_list)
    return rgb2hex(*[i for i in rgb], normalised=True)


def fix_map_colours(apps, schema_editor):
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
        aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
    )
    for map in KnowledgeMapModel.objects.all():
        map_json = json.loads(map.retrieve_map().decode("utf-8"))
        print(f"\n{map.url_extension}")
        for count, node in enumerate(map_json["nodes"]):
            node_data = node["data"]
            if node_data["nodetype"] == "field":
                print(f'{node_data["name"]}: {node_data["colour"]}')
                new_colour = COLOUR_MAP.get(
                    node_data["colour"], darken_hex(node_data["colour"], 0.25)
                )
                print(f'{node_data["name"]} new colour: {new_colour}')
                map_json["nodes"][count]["data"]["colour"] = new_colour
        s3.Bucket(map.s3_bucket_name).put_object(Key=map.s3_key, Body=json.dumps(map_json))
        map.version += 1
        map.save()


def revert_map_colours(apps, schema_editor):
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
        aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
    )
    for map in KnowledgeMapModel.objects.all():
        map_json = json.loads(map.retrieve_map().decode("utf-8"))
        print(f"\n{map.url_extension}")
        for count, node in enumerate(map_json["nodes"]):
            node_data = node["data"]
            if node_data["nodetype"] == "field":
                print(f'{node_data["name"]}: {node_data["colour"]}')
                new_colour = REVERTED_COLOUR_MAP.get(
                    node_data["colour"], darken_hex(node_data["colour"], 4)
                )
                print(f'{node_data["name"]} new colour: {new_colour}')
                map_json["nodes"][count]["data"]["colour"] = new_colour
        s3.Bucket(map.s3_bucket_name).put_object(Key=map.s3_key, Body=json.dumps(map_json))
        map.version += 1
        map.save()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0002_knowledgemapmodel_allow_suggestions"),
    ]

    operations = [migrations.RunPython(fix_map_colours, reverse_code=revert_map_colours)]
