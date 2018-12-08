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
    #  玩法记录下俱乐部
    path('mark/club/', views.MarkClubView.as_view(), name="record-mark-club"),
    #  月份
    path('club/month/', views.ClubMonthView.as_view(), name="club-month"),
    #  首页
    path('club/home/', views.ClubHomeView.as_view(), name="club-home"),
    #  俱乐部充值提现明细
    path('club/pay/', views.PayClubView.as_view(), name="club-pay"),
    #  俱乐部用户列表
    path('club/user/', views.ClubUserView.as_view(), name="club-user-list"),
    #  俱乐部投注列表
    path('club/bet/list/', views.ClubBetListView.as_view(), name="club-bet-list"),
    #  盈利奖励
    path('club/bets/', views.ClubBetsView.as_view(), name="club-bets-list"),
    #  俱乐部用户详情
    path('club/user/info/', views.ClubUserInfoView.as_view(), name="club-user-info"),
    #  单天投注
    path('club/day/bet/', views.ClubDayBetView.as_view(), name="club-day-bet"),
]
