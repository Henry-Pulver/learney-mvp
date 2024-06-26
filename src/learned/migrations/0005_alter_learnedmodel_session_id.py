# Generated by Django 3.2.2 on 2021-10-19 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("learned", "0004_rename_last_updated_learnedmodel_timestamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="learnedmodel",
            name="session_id",
            field=models.TextField(
                blank=True, help_text="session_key of the session that the concept was learned in"
            ),
        ),
    ]
