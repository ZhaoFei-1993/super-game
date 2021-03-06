# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    # 俱乐部列表
    path('club_backend_list/', views.ClubBackendListView.as_view(), name='chat-club_backend_list'),
    # 俱乐部详情
    path('club_backend_list/<int:pk>/', views.ClubBackendListDetailView.as_view(), name='chat-club_backend_list'),
    # 俱乐部排序
    path('club_backend_sort/', views.ClubBackendSortView.as_view(), name='chat-club_backend_sort'),
    # 轮播图列表
    path('banner_list/', views.BannerImage.as_view(), name='chat-banner_list'),
    # 轮播图详情
    path('banner_list/<int:pk>/', views.BannerImageDetail.as_view(), name='chat-banner_detail'),
    # 玩法列表
    path('club_rule_list/', views.ClubRuleList.as_view(), name='chat-club_rule_list'),
    # 玩法列表详情
    path('club_rule_list/<int:pk>/', views.ClubRuleDetail.as_view(), name='chat-club_rule_detail'),
    # 货币数据
    path('coins/', views.CoinsList.as_view(), name='backend-coin-data'),
    # 做庄俱乐部选择列表
    path('club/banker/', views.ClubBankerList.as_view(), name='user—club-banker'),
    # 俱乐部局头记录
    path('banker/record/', views.ClubBankerRecord.as_view(), name='club-banker-record'),
    # 俱乐部散户局头开关
    path('banker/switch/', views.ClubBankerSwitchView.as_view(), name='club-banker-switch'),
    # 做庄局头操作
    path('user/banker/', views.UserBanker.as_view(), name='club-user-banker'),
    # 设置局头管理员
    path('club/income/', views.ClubIncome.as_view(), name='club-income-user'),
    # 局头转账
    path('club/income/record/', views.ClubIncomeRecord.as_view(), name='club-income-record'),
]
