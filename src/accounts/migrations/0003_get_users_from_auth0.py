# Generated by Django 3.2.2 on 2022-01-05 18:10
import json
from typing import Dict

from django.db import migrations, models

import boto3
from learney_web.settings import AWS_CREDENTIALS, IS_PROD

S3_FILENAME = "dev-3sm9ewzj.json"


def user_data_download_to_user_db_object(user_data: Dict) -> Dict:
    return {
        "id": user_data["Id"],
        "name": user_data["Name"],
        "nickname": user_data["Nickname"],
        "picture": user_data["Picture"],
        "given_name": "",
        "family_name": "",
        "locale": "",
    }


def get_users():
    # GET json file from S3
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=AWS_CREDENTIALS["ACCESS_ID"],
        aws_secret_access_key=AWS_CREDENTIALS["SECRET_KEY"],
    )
    response = s3.Object("learney-prod", S3_FILENAME).get()
    return json.loads(response["Body"].read())


def add_auth0_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    users = get_users()

    for user_data in users:
        if IS_PROD:
            User.objects.create(**user_data_download_to_user_db_object(user_data))


def delete_auth0_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    users = get_users()

    for user_data in users:
        if IS_PROD and User.objects.filter(id=user_data["Id"]).count() > 0:
            User.objects.get(id=user_data["Id"]).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [("accounts", "0002_upload_user_profiles_to_mixpanel")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="picture",
            field=models.URLField(max_length=1000),
        ),
        migrations.RunPython(add_auth0_data, reverse_code=delete_auth0_data),
    ]
