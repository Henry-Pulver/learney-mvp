# Generated by Django 3.2.2 on 2021-06-02 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LearnedModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("user_id", models.TextField()),
                ("learned_concepts", models.JSONField()),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
