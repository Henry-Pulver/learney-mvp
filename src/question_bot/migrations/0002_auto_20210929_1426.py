# Generated by Django 3.2.2 on 2021-09-29 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("question_bot", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="answermodel",
            old_name="user_id",
            new_name="user_email",
        ),
        migrations.RenameField(
            model_name="questionlastaskedmodel",
            old_name="user_id",
            new_name="user_email",
        ),
        migrations.RenameField(
            model_name="slackbotusermodel",
            old_name="user_id",
            new_name="user_email",
        ),
    ]
