# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 发送手机短信验证码共用接口       已测试
    path('code/', views.SmsView.as_view(), name="sms-code"),
    # 校验手机短信验证码是否有效。
    path('code/verify/', views.SmsVerifyView.as_view(), name="sms-code-verify"),
    # 轮播图。
    path('announcement/carousel_map/', views.CarouselMapVerifyView.as_view(), name="announcement-carousel-map"),
    # 公告列表。
    path('announcement/list/', views.ListVerifyView.as_view(), name="announcement-list"),
    # 公告详情。
    path('announcement/info/', views.InfoVerifyView.as_view(), name="announcement-info"),
]
