from django.apps import AppConfig
from django.core.signals import setting_changed


class VideosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'videos'

