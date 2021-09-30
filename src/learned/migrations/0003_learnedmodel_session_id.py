# Generated by Django 3.2.2 on 2021-09-27 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learned", "0002_learnedmodel_map_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="learnedmodel",
            name="session_id",
            field=models.TextField(
                blank=True,
                editable=False,
                help_text="session_key of the session that the concept was learned in",
            ),
        ),
    ]