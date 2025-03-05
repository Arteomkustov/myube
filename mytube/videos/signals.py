from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Videos
from .utils import convert  # Импортируйте вашу функцию конвертации


@receiver(pre_save, sender=Videos)
def convert_video_before_save(sender, instance, **kwargs):
    if instance.video_file:  # Предположим, что `video_file` - это название поля с файлом видео в вашей модели
        output_file = 'path/to/converted/video.mp4'  # Укажите путь для сохранения конвертированного видео
        convert(instance.video_file.path, output_file)
        instance.converted_video_file = output_file  # Запишите путь к конвертированному видео в соответствующее поле
