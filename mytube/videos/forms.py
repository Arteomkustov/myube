from django import forms

from .models import Videos, Channel, Comment


class AddVideoForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input'}), label="Название")

    class Meta:
        model = Videos
        fields = ['title', 'overview', 'banner', 'video_file', ]
        labels = {
            'overview': 'Описание',
            'banner': 'Изображение',
            'video_file': 'Видеофайл'
        }


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'overview', 'small_image', 'large_image']


class SubscriptionForm(forms.Form):
    channel_id = forms.IntegerField(widget=forms.HiddenInput())


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class SearchForm(forms.Form):
    query = forms.CharField(label='Поиск', max_length=255)
