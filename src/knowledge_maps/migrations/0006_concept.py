# Generated by Django 3.2.2 on 2022-01-27 12:12

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_maps", "0005_auto_20220110_1504"),
    ]

    operations = [
        migrations.CreateModel(
            name="Concept",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, help_text="Unique id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Description of the knowledge map shown in top left corner",
                        max_length=256,
                    ),
                ),
                (
                    "cytoscape_id",
                    models.CharField(
                        help_text="The id of the concept in the questions map cytoscape map json file",
                        max_length=4,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
