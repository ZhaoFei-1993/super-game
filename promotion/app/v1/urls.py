# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 用户邀请信息界面
    path('promotion/info/', views.PromotionInfoView.as_view(), name="promotion-invitation-info"),
    # 邀请俱乐部流水
    path('promotion/list/', views.PromotionListView.as_view(), name="promotion-invitation-list"),
    # 收入
    path('club/promotion/', views.PromotioncClubView.as_view(), name="promotion-invitation-club"),
    # 玩法列表
    path('club/rule/', views.ClubRuleView.as_view(), name="promotion-club-rule"),
    # 流水明细
    path('club/detail/', views.ClubDetailView.as_view(), name="promotion-club-detail"),
    # 分成明细
    path('club/dividend/', views.ClubDividendView.as_view(), name="promotion-club-dividend"),
    # 我的客人
    path('customer/', views.CustomerView.as_view(), name="promotion-club-customer"),
    # 用户详情
    path('user/info/', views.UserInfoView.as_view(), name="promotion-user-info"),
]
