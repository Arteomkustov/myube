from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('video/<slug>/', views.video, name='video'),
    path('search/', views.search, name='search'),
    path('updatevideo/<slug>/', views.DescriptionUpdateView.as_view(), name='updatevideo'),
    path('updateoverview/', views.OverviewUpdateView.as_view(), name='updateoverview'),
    path("chanel/<slug:slug>/", views.ChanelDetailView.as_view(), name="chanel"),
    path('addvideo/', views.add_video, name='addvideo'),
    path('channels/', views.channel_list, name='channel_list'),
    path('channels/create/', views.create_channel, name='create_channel'),
    path('channels/subscribe/<int:channel_id>/', views.subscribe, name='subscribe'),
    path('channels/unsubscribe/<int:channel_id>/', views.unsubscribe, name='unsubscribe'),
    path('mychannel/', views.mychannel, name='mychannel'),
    path('watch/<slug>/', views.video_detail, name='video_detail'),
]