# Generated by Django 3.2.2 on 2022-01-27 12:12
import json

from django.db import migrations

from learney_web.settings import AWS_CREDENTIALS
from learney_web.utils import retrieve_map_from_s3


def add_concepts_from_questions_map(apps, schema_editor):
    Concept = apps.get_model("knowledge_maps", "Concept")
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    map_q_set = KnowledgeMapModel.objects.filter(url_extension="original_map")
    if map_q_set.exists():
        map = map_q_set.first()
    else:
        map = KnowledgeMapModel.objects.create(
            url_extension="questionsmap",
            s3_bucket_name="learney-test",
            s3_key="questions_map.json",
            author_user_id="henrypulver13@gmail.com",
        )
    map_json = json.loads(retrieve_map_from_s3(map.s3_bucket_name, map.s3_key, AWS_CREDENTIALS))

    # Add all the concepts
    for node in map_json["nodes"]:
        node_data = node["data"]
        if node_data["nodetype"] == "concept":
            Concept.objects.create(
                name=node_data["name"],
                cytoscape_id=node_data["id"],
            )

    # Add all the edges
    for edge in map_json["edges"]:
        edge_data = edge["data"]
        source_concept = Concept.objects.get(cytoscape_id=edge_data["source"])
        target_concept = Concept.objects.get(cytoscape_id=edge_data["target"])
        target_concept.direct_prerequisites.add(source_concept)


def delete_all_concepts(apps, schema_editor):
    Concept = apps.get_model("knowledge_maps", "Concept")
    for concept in Concept.objects.all():
        concept.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0006_concept"),
    ]

    operations = [
        migrations.RunPython(add_concepts_from_questions_map, reverse_code=delete_all_concepts)
    ]
