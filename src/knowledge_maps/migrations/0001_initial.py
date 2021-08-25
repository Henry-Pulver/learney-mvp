# Generated by Django 3.2.2 on 2021-08-19 11:20

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []  # type: ignore

    operations = [
        migrations.CreateModel(
            name="KnowledgeMapModel",
            fields=[
                (
                    "unique_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        help_text="Unique identifier for each knowledge map",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "author_user_id",
                    models.TextField(help_text="User ID of user who created this map"),
                ),
                (
                    "url_extension",
                    models.TextField(help_text="URL extension of the map", unique=True),
                ),
                (
                    "s3_bucket_name",
                    models.TextField(
                        help_text="Name of the S3 bucket that the knowledge map json is stored in"
                    ),
                ),
                ("s3_key", models.TextField(help_text="Key of the knowledge map json in S3")),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("version", models.IntegerField(default=0, help_text="Version number of the map")),
            ],
        ),
    ]