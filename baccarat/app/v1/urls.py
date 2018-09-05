# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  游戏详情
    path('table/boots/', views.Table_boots.as_view(), name="dragon-tiger-table-boots"),
    # 下注
    path('bet/', views.DragontigerBet.as_view(), name="dragon-tiger-bet"),
    # 记录
    path('record/', views.Record.as_view(), name="dragon-tiger-record"),
    # 换桌
    path('change_table/', views.Changetable.as_view(), name="dragon-tiger-change-table"),
    ## 头像
    # path('bet/avatar/', views.Avatar.as_view(), name="dragon-tiger-avatar"),
]
