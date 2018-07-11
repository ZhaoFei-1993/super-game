# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    # 俱乐部列表
    path('club_backend_list/', views.ClubBackendListView.as_view(), name='chat-club_backend_list'),
    # 俱乐部详情
    path('club_backend_list/<int:pk>/', views.ClubBackendListDetailView.as_view(), name='chat-club_backend_list'),
    # 轮播图列表
    path('banner_list/', views.BannerImage.as_view(), name='chat-banner_list'),
    # 轮播图详情
    path('banner_list/<int:pk>/', views.BannerImageDetail.as_view(), name='chat-banner_detail'),
    # 玩法列表
    path('club_rule_list/', views.ClubRuleList.as_view(), name='chat-club_rule_list'),
    # 玩法列表详情
    path('club_rule_list/<int:pk>/', views.ClubRuleDetail.as_view(), name='chat-club_rule_detail'),
]
