# Generated by Django 3.2.2 on 2022-01-27 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_checked_content_links"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="in_questions_trial",
            field=models.BooleanField(
                default=False, help_text="Whether or not they're involved in the question trial"
            ),
        ),
    ]
