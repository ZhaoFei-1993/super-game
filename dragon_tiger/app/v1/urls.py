# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  登录获取桌子信息
    path('table/info/', views.Table_info.as_view(), name="dragon-tiger-login-table-info"),
    #  模拟post进行url请求
    path('request_post/', views.Request_post.as_view(), name="dragon-tiger-request-post"),
    #  龙虎斗：选项
    path('option/info/', views.Dragontigeroption.as_view(), name="dragon-tiger-option-info"),
    # 下注
    path('bet/', views.DragontigerBet.as_view(), name="dragon-tiger-bet"),
]
