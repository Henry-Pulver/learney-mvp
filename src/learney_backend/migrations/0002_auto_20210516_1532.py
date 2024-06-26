# Generated by Django 3.2 on 2021-05-16 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learney_backend", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="contentlinkpreview",
            old_name="last_retrieved",
            new_name="preview_last_retrieved",
        ),
        migrations.AddField(
            model_name="contentvote",
            name="concept",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="contentvote",
            name="url",
            field=models.URLField(unique=True),
        ),
    ]
