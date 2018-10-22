# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  俱乐部列表
    # path('clublist/', views.ClublistView.as_view(), name="chat-club-list"),
    # 联合坐庄：   玩法
    path('banker/rule/', views.BankerRuleView.as_view(), name="banker_rule"),
    # 联合坐庄：   俱乐部
    path('banker/club/', views.BankerClubView.as_view(), name='banker_club'),
    # 联合坐庄：   坐庄
    # path('banker/detail/', views.BankerDetailView.as_view(), name='banker_detail'),

]
