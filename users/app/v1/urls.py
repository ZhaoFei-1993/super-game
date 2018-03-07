# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    #用户列表
    path('list/', views.ListView.as_view(), name="app-v1-user-list"),
    # 首页----设置页面（并用）
    path('info/', views.InfoView.as_view(), name="app-v1-user-info"),
    # 注册,登录接口        已测试
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
    # 排行榜
    path('ranking/', views.RankingView.as_view(), name="app-v1-user-ranking"),
    # 我的资产
    path('assets/', views.AssetsView.as_view(), name="app-v1-user-assets"),
    # 用户退出登录           未测试
    path('logout/', views.LogoutView.as_view(), name="app-v1-user-logout"),
]

