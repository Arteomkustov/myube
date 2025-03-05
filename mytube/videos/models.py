from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from django.utils.text import slugify

from mytube.settings import SERVER_IP


def unique_slugify(instance, slug):
    """
    Генератор уникальных SLUG для моделей, в случае существования такого SLUG.
    """
    model = instance.__class__
    unique_slug = slugify(slug)
    while model.objects.filter(slug=unique_slug).exists():
        unique_slug = f'{unique_slug}-{uuid4().hex[:8]}'
    unique_slug = f'{unique_slug}-{uuid4().hex[:8]}'
    return unique_slug


class Videos(models.Model):
    title = models.TextField(max_length=250, verbose_name="Название")
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)
    overview = models.TextField(verbose_name="Описание")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    video_file = models.FileField(upload_to='videos/', validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'webm', 'flv', 'mkv'])])
    converted_video_file_144 = models.FileField(upload_to='videos/', null=True, default=None)
    converted_video_file_380 = models.FileField(upload_to='videos/', null=True, default=None)
    converted_video_file_720 = models.FileField(upload_to='videos/', null=True, default=None)
    banner = models.ImageField(null=True)
    subtitles = models.FileField(upload_to='videos/', null=True, default=None)
    ready = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.slug == None or self.slug == '':
            self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('video_detail', kwargs={'slug': self.slug})

    def get_edit_url(self):
        return reverse('updatevideo', kwargs={'slug': self.slug})

    def get_absolute_video_url(self):
        return SERVER_IP + reverse('video', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


class Channel(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, unique=True)
    name = models.CharField(max_length=255)
    overview = models.TextField()
    small_image = models.ImageField(upload_to='channel_images/small/')
    large_image = models.ImageField(upload_to='channel_images/large/')
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('chanel', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'channel')

    def __str__(self):
        return f"{self.user.username} -> {self.channel.name}"


class Comment(models.Model):
    video = models.ForeignKey(Videos, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return


class LikeDislike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VOTE_CHOICES = (
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike')
    )

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    video = models.ForeignKey(Videos, on_delete=models.CASCADE, related_name='votes')
    vote = models.SmallIntegerField(choices=VOTE_CHOICES, null=True, default=1)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user.username}: {self.get_vote_display()} - {self.video.title}"


class VideoView(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    video = models.ForeignKey(Videos, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} viewed {self.video.title}"


class Recommendation(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, blank=True)
    video = models.ForeignKey(Videos, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation for {self.user.username if self.user else 'Anonymous'}: {self.video.title}"






