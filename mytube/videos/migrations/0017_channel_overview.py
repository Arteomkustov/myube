# Generated by Django 5.1.6 on 2025-02-23 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0016_videos_views'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='overview',
            field=models.TextField(default='qwqeqer'),
        ),
    ]
