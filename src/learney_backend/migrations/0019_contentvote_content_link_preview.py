# Generated by Django 3.2.2 on 2021-12-22 20:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learney_backend", "0018_map_uuid_to_map"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentvote",
            name="content_link_preview",
            field=models.ForeignKey(
                help_text="The ContentLinkPreview that was voted on",
                related_name="votes",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="learney_backend.contentlinkpreview",
            ),
        ),
    ]
