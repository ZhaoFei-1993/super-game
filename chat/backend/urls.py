# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    #俱乐部列表
    path('club_backend_list/', views.ClubBackendListView.as_view(), name='chat-club_backend_list'),
    #俱乐部详情
    path('club_backend_list/<int:pk>/', views.ClubBackendListDetailView.as_view(), name='chat-club_backend_list'),
]

