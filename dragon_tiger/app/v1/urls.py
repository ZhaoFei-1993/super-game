# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  桌子列表
    path('table/list/', views.Table_list.as_view(), name="dragon-tiger-table-list"),
    #  游戏详情
    path('table/boots/', views.Table_boots.as_view(), name="dragon-tiger-table-boots"),
    #  龙虎斗：选项
    path('option/info/', views.Dragontigeroption.as_view(), name="dragon-tiger-option-info"),
    # 下注
    path('bet/', views.DragontigerBet.as_view(), name="dragon-tiger-bet"),
]
