from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import UpdateView, DetailView

from .forms import AddVideoForm, ChannelForm, CommentForm
from .models import Videos, Channel, Subscription, LikeDislike, VideoView
from .utils import process_and_save_video, get_client_ip, search, add_video_view, get_hybrid_recommendations, \
    get_collaborative_recommendations, home_recomendation, get_random_videos
from django.contrib.auth.decorators import login_required


# Create your views here.


def home(request):
    # u = get_user_model().objects.get(pk=1).subscription_pk #.channel
    if request.user.is_authenticated:
        rec = home_recomendation(request.user)
    else:
        rec = get_random_videos()
    data = {
        'rec': rec,
    }
    return render(request, 'index.html', data)


@xframe_options_exempt
def video(request, slug):
    a = get_object_or_404(Videos, slug=slug, ready=True)
    print(a.converted_video_file_720.url)
    return render(request, 'video.html', {'data': a})


@xframe_options_exempt
@login_required
def add_video(request):
    if not Channel.objects.filter(user=request.user).exists():
        return redirect('create_channel')  # Перенаправление на создание канала, если у пользователя его нет

    channel = Channel.objects.get(user=request.user)

    if request.method == 'POST':
        form = AddVideoForm(request.POST, request.FILES)
        if form.is_valid():
            print(1)
            video = form.save(commit=False)
            video.channel = channel
            video.save()
            input_path = video.video_file.name
            process_and_save_video(input_path, video)
            return redirect('addvideo')
        print(form.errors)

    else:
        form = AddVideoForm()
    data = {
        'form': form
    }
    return render(request, 'add-video.html', data)


@login_required
def create_channel(request):
    if Channel.objects.filter(user=request.user).exists():
        return redirect('mychannel')

    if request.method == 'POST':
        form = ChannelForm(request.POST, request.FILES)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.user = request.user
            channel.save()
            return redirect('mychannel')
        print(form.e)
    else:
        form = ChannelForm()
    return render(request, 'create_channel.html', {'form': form})


@login_required
def channel_list(request):
    user_channel = Channel.objects.filter(user=request.user).first()
    subscriptions = Subscription.objects.filter(user=request.user)
    all_channels = Channel.objects.exclude(user=request.user)
    return render(request, 'channel_list.html', {
        'user_channel': user_channel,
        'subscriptions': subscriptions,
        'all_channels': all_channels
    })


@login_required
def subscribe(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    if not Subscription.objects.filter(user=request.user, channel=channel).exists():
        Subscription.objects.create(user=request.user, channel=channel)
    return redirect('chanel', slug=channel.slug)


@login_required
def unsubscribe(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    Subscription.objects.filter(user=request.user, channel=channel).delete()
    return redirect('chanel', slug=channel.slug)


@method_decorator(xframe_options_exempt, name='dispatch')
class DescriptionUpdateView(LoginRequiredMixin, UpdateView):
    model = Videos
    fields = ["overview"]
    template_name = "update_video.html"

    def get_object(self, queryset=None):
        # print(self.kwargs['slug'], self.request.user.channel.pk)
        o = get_object_or_404(Videos, slug=self.kwargs['slug'], channel_id=self.request.user.channel.pk)
        return o


class ChanelDetailView(DetailView):
    model = Channel # -------------------------------------------------------------------------------------------------------------
    template_name = 'channel_detail.html'

    def get_context_data(self, **kwargs):
        channel = get_object_or_404(Channel, slug=self.kwargs['slug'])
        videos = Videos.objects.filter(channel=channel, ready=True).order_by('-created_at')
        subscribers = Subscription.objects.filter(channel=channel)
        subscribers_count = subscribers.count()
        fl = False
        for i in subscribers:
            if self.request.user.is_authenticated and i.user_id == self.request.user.id:
                fl = True
                #print(1)
        context = super().get_context_data(**kwargs)
        context['videos'] = videos
        context['subscribers_count'] = subscribers_count
        context['subscribe'] = fl
        return context


@method_decorator(xframe_options_exempt, name='dispatch')
class OverviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Channel
    fields = ["overview"]
    template_name = "update_video.html"

    def get_object(self, queryset=None):
        # print(self.kwargs['slug'], self.request.user.channel.pk)
        o = get_object_or_404(Channel, id=self.request.user.channel.pk)
        return o


# @login_required
def video_detail(request, slug):
    video = get_object_or_404(Videos, slug=slug, ready=True)
    comments = video.comments.all()
    comment_form = CommentForm()
    add_video_view(request, video)
    subscribers = Subscription.objects.filter(channel=video.channel)
    fl = False
    for i in subscribers:
        if request.user.is_authenticated and i.user_id == request.user.id:
            fl = True

    if request.user.is_authenticated:
        recommendations = get_hybrid_recommendations(request.user, video)
    else:
        recommendations = get_random_videos()

    client_ip = get_client_ip(request)
    if True:
        VideoView.objects.create(video=video, ip_address=client_ip)
        video.views += 1
        video.save()

    if request.method == 'POST' and 'text' in request.POST:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.video = video
            comment.user = request.user
            comment.save()
            return redirect('video_detail', slug=slug)

    if request.method == 'POST' and 'like' in request.POST:
        handle_vote(request, video, 1)

    if request.method == 'POST' and 'dislike' in request.POST:
        handle_vote(request, video, -1)

    return render(request, 'video_detail.html', {
        'video': video,
        'comments': comments,
        'comment_form': comment_form,
        'recomendation': recommendations,
        'subscribers': fl,
    })


def handle_vote(request, video, vote_value):
    try:
        # print('llil', vote_value)
        like_dislike, created = LikeDislike.objects.get_or_create(user=request.user, video=video)
        # print(video.like_dislike)
        # like_dislike.vote = vote_value
        # like_dislike.save()
        if vote_value == 1:
            if not created:
                if like_dislike.vote == 1:
                    like_dislike.vote = 2
                    video.likes -= 1
                elif like_dislike.vote == 2:
                    like_dislike.vote = 1
                    video.likes += 1
                elif like_dislike.vote == -1:
                    like_dislike.vote = 1
                    video.likes += 1
                    video.dislikes -= 1
                elif like_dislike.vote == -2:
                    like_dislike.vote = 1
                    video.likes += 1
                pass
            else:
                video.likes += 1
                like_dislike.vote = vote_value
            # video.likes += 1
            # video.dislikes -= 1 if not created and like_dislike.vote == 1 else 0
        else:
            if not created:
                if like_dislike.vote == -1:
                    like_dislike.vote = -2
                    video.dislikes -= 1
                elif like_dislike.vote == -2:
                    like_dislike.vote = -1
                    video.dislikes += 1
                elif like_dislike.vote == 1:
                    like_dislike.vote = -1
                    video.likes -= 1
                    video.dislikes += 1
                elif like_dislike.vote == 2:
                    like_dislike.vote = -1
                    video.dislikes += 1
                pass
            else:
                video.dislikes += 1
                like_dislike.vote = vote_value
            # video.dislikes += 1
            # video.likes -= 1 if not created and like_dislike.vote == -1 else 0
        like_dislike.save()
        video.save()
    except Exception as e:
        print(f"Error handling vote: {e}")


from django.shortcuts import render
from fuzzywuzzy import fuzz

from .forms import SearchForm

def search(request):
    query = request.GET.get('query')
    videos = []
    channels = []

    if query:
        all_videos = Videos.objects.filter(ready=True)
        all_channels = Channel.objects.all()

        for video in all_videos:
            if fuzz.partial_ratio(query.lower(), video.title.lower()) >= 70 or fuzz.partial_ratio(query.lower(), video.overview.lower()) >= 70:
                videos.append(video)

        for channel in all_channels:
            if fuzz.partial_ratio(query.lower(), channel.name.lower()) >= 70 or fuzz.partial_ratio(query.lower(), channel.overview.lower()) >= 70:
                channels.append(channel)

    return render(request, 'search_results.html', {
        'query': query,
        'videos': videos,
        'channels': channels,
    })


@login_required
def mychannel(request):
    try:
        channel = Channel.objects.get(user=request.user)
    except Channel.DoesNotExist:
        return redirect('create_channel')
    # channel = get_object_or_404(Channel, user=request.user)
    videos = Videos.objects.filter(channel=channel).order_by('-created_at')
    subscribers_count = Subscription.objects.filter(channel=channel).count()

    if request.method == 'POST':
        video_id = request.POST.get('video_id')
        video = get_object_or_404(Videos, id=video_id, channel=channel)
        video.delete()
        return redirect('mychannel')

    return render(request, 'mychannel.html', {'channel': channel, 'videos': videos, 'subscribers_count': subscribers_count})
