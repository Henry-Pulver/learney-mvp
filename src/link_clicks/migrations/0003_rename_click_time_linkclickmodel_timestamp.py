# Generated by Django 3.2.2 on 2021-09-30 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("link_clicks", "0002_auto_20210927_1958"),
    ]

    operations = [
        migrations.RenameField(
            model_name="linkclickmodel",
            old_name="click_time",
            new_name="timestamp",
        ),
        migrations.AlterField(
            model_name="linkclickmodel",
            name="url",
            field=models.URLField(help_text="URL of link that was clicked"),
        ),
    ]
