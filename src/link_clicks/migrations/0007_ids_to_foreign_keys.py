# Generated by Django 3.2.2 on 2021-12-22 14:49

import django.db.models.deletion
from django.db import migrations, models


def populate_map_field(apps, schema_editor):
    KnowledgeMapModel = apps.get_model("knowledge_maps", "KnowledgeMapModel")
    LinkClickModel = apps.get_model("link_clicks", "LinkClickModel")
    for link_click_entry in LinkClickModel.objects.all():
        link_click_entry.map = KnowledgeMapModel.objects.get(unique_id=link_click_entry.map_uuid)
        link_click_entry.save()


def populate_map_uuid_field(apps, schema_editor):
    LinkClickModel = apps.get_model("link_clicks", "LinkClickModel")
    for link_click_entry in LinkClickModel.objects.all():
        link_click_entry.map_uuid = link_click_entry.map.unique_id
        link_click_entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0004_fix_underscore_issue_name_id"),
        ("link_clicks", "0006_migrate_old_data_to_mixpanel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="linkclickmodel",
            name="timestamp",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name="linkclickmodel",
            name="map",
            field=models.ForeignKey(
                help_text="Map this link click corresponds to",
                related_name="link_clicks",
                on_delete=django.db.models.deletion.CASCADE,
                to="knowledge_maps.knowledgemapmodel",
                null=True,
            ),
        ),
        migrations.RunPython(populate_map_field, reverse_code=populate_map_uuid_field),
        migrations.RemoveField(
            model_name="linkclickmodel",
            name="map_uuid",
        ),
        migrations.AlterField(
            model_name="linkclickmodel",
            name="map",
            field=models.ForeignKey(
                help_text="Map this link click corresponds to",
                related_name="link_clicks",
                on_delete=django.db.models.deletion.CASCADE,
                to="knowledge_maps.knowledgemapmodel",
            ),
        ),
    ]
