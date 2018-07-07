# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  俱乐部列表
    path('clublist/', views.ClublistView.as_view(), name="chat-club-list"),
    #  俱乐部模糊搜索
    path('club/search/', views.ClubSearchView.as_view(), name="chat-club-search"),
]
