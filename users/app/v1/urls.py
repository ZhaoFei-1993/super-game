# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('list/', views.ListView.as_view(), name="app-v1-user-list"),
    path('info/', views.InfoView.as_view(), name="app-v1-user-info"),
    # 注册,登录接口        已测试
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
    # 用户退出登录           未测试
    path('logout/', views.LogoutView.as_view(), name="app-v1-user-logout"),
]

