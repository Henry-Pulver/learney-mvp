"""Add ContentLinkPreviews for each link in the map.

Even if linkpreview.net fails, we want an empty preview to exist.
"""
import json

from django.db import migrations

from knowledge_maps.views import retrieve_map
from learney_backend.utils import get_from_linkpreview_net


def add_content_link_previews(apps, schema_editor):
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    ContentLinkPreview = apps.get_model("learney_backend", "ContentLinkPreview")
    for map in KnowledgeMapModel.objects.all():
        map_json = json.loads(retrieve_map(map).decode("utf-8"))
        print(f"\n{map.url_extension}")
        for node in map_json["nodes"]:
            node_data = node["data"]
            for url in node_data.get("urls", []):
                url_matches = ContentLinkPreview.objects.filter(url=url)
                # Check - does this exact link preview (link + map id) exist already?
                exact_matches = url_matches.filter(map=map, concept_id=node_data["id"])
                if exact_matches.count() > 0:
                    # If so, update concept name
                    most_recent_match = exact_matches.latest("preview_last_updated")
                    if most_recent_match.concept != node_data["name"]:
                        most_recent_match.concept = node_data["name"]
                        most_recent_match.save()
                    continue

                db_dict = {
                    "map": map,
                    "concept": node_data["name"],
                    "concept_id": node_data["id"],
                    "url": url,
                }
                if url_matches.count() == 0:  # New URL
                    db_dict = get_from_linkpreview_net(db_dict)
                else:  # URL exists in DB, but not right ContentLinkPreview
                    best_match = url_matches.latest("preview_last_updated")
                    db_dict.update(
                        {
                            "title": best_match.title,
                            "description": best_match.description,
                            "image_url": best_match.image_url,
                        }
                    )
                ContentLinkPreview(**db_dict).save()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0005_auto_20220110_1504"),
        ("learney_backend", "0019_contentvote_content_link_preview"),
    ]

    operations = [
        migrations.RunPython(add_content_link_previews, reverse_code=migrations.RunPython.noop)
    ]
