# Generated by Django 3.2.2 on 2021-06-02 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learney_backend', '0004_auto_20210601_2052'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentvote',
            name='user_id',
            field=models.TextField(default=''),
        ),
    ]
