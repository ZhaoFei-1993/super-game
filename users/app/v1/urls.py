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
    # 排行榜       已经测试
    path('ranking/', views.RankingView.as_view(), name="app-v1-user-ranking"),
    # 我的资产
    path('assets/', views.AssetsView.as_view(), name="app-v1-user-assets"),
    # 用户退出登录           未测试
    path('logout/', views.LogoutView.as_view(), name="app-v1-user-logout"),
    # 密保校验 用户绑定密保  and   修改密保           已测试
    path('modify_security/<int:type>/', views.SecurityView.as_view(), name="app-v1-user-modify-security"),
    # 忘记密保
    path('back_security/', views.BackSecurityView.as_view(), name="app-v1-user-back-security"),
    # 音效/消息免推送 开关
    path('switch/', views.SwitchView.as_view(), name="app-v1-user-switch"),
]

