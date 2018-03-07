# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    # 发送手机短信验证码共用接口       已测试
    path('code/', views.SmsView.as_view(), name="sms-code"),
    # 校验手机短信验证码是否有效。
    path('code/', views.SmsVerifyView.as_view(), name="sms-code-verify"),
]

