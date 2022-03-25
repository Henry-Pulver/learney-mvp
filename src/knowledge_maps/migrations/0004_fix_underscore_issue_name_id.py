import json

from django.db import migrations

import boto3
from learney_web.settings import AWS_CREDENTIALS
from learney_web.utils import retrieve_map_from_s3


def fix_topic_id_underscores(apps, schema_editor):
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
        aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
    )
    for map in KnowledgeMapModel.objects.all():
        map_json = json.loads(
            retrieve_map_from_s3(map.s3_bucket_name, map.s3_key, AWS_CREDENTIALS).decode("utf-8")
        )
        print(f"\n{map.url_extension}")
        invalid_indexes = []
        for count, node in enumerate(map_json["nodes"]):
            node_data = node["data"]
            if node_data.get("nodetype") is None:
                invalid_indexes.append(count)

            if node_data.get("nodetype") == "field":
                prev_topic_id = node_data["id"]
                new_topic_name = node_data["name"].replace("_", " ")
                print(
                    f'{node_data["name"]} | prev id: {prev_topic_id} | new id: {new_topic_name}\n'
                )
                map_json["nodes"][count]["data"]["name"] = new_topic_name
                map_json["nodes"][count]["data"]["id"] = new_topic_name

                for count_2, node_2 in enumerate(map_json["nodes"]):
                    if (
                        node_2["data"].get("nodetype") == "concept"
                        and node_2["data"].get("parent") == prev_topic_id
                    ):
                        # print(f'{node_2["data"]["name"]} | prev parent: {node_2["data"]["parent"]} | new id: {new_topic_name}')
                        map_json["nodes"][count_2]["data"]["parent"] = new_topic_name
        for index in reversed(invalid_indexes):
            map_json["nodes"].remove(map_json["nodes"][index])
        s3.Bucket(map.s3_bucket_name).put_object(Key=map.s3_key, Body=json.dumps(map_json))
        map.version += 1
        map.save()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0003_fix_map_colours"),
    ]

    operations = [
        migrations.RunPython(fix_topic_id_underscores, reverse_code=migrations.RunPython.noop)
    ]
