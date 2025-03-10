# Generated by Django 5.1.6 on 2025-02-22 14:44

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0003_videos_ready_alter_videos_converted_video_file_144_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='videos',
            name='subtitles',
            field=models.FileField(default=None, null=True, upload_to='videos/'),
        ),
        migrations.AlterField(
            model_name='videos',
            name='video_file',
            field=models.FileField(upload_to='videos/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'webm', 'flv', 'mkv'])]),
        ),
    ]
