# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  俱乐部列表
    path('clublist/', views.ClublistView.as_view(), name="chat-club-list"),
    #  俱乐部内玩法列表
    path('club/rule/', views.ClubRuleView.as_view(), name="chat-club-rule"),
    #  俱乐部轮播图
    path('club/banner/', views.BannerView.as_view(), name="chat-club-banner"),
]
