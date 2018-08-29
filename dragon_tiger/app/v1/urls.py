# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  登录获取加密串
    path('dragon_tiger/login/', views.Encryption.as_view(), name="dragon-tiger-login"),
    #  模拟post进行url请求
    path('request_post/', views.Request_post.as_view(), name="dragon-tiger-request-post"),
    #  龙虎斗：选项
    path('option/info/', views.Dragontigeroption.as_view(), name="dragon-tiger-option-info"),
]
