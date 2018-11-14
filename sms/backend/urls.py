# -*- coding: UTF-8 -*-
from django.urls import path
from sms.backend import views

urlpatterns = [
    # 发送手机短信验证码共用接口       已测试
    path('code/', views.SmsView.as_view(), name="sms-backend-code"),
    # 校验手机短信验证码是否有效。
    path('code/verify/', views.SmsVerifyView.as_view(), name="sms-backend-code-verify"),
    # 公告列表
    path('announcement/list/', views.AnnouncementVerifyView.as_view(), name="backend-announcement-list"),
    # 公告管理
    path('announcement/info/', views.AnnouncementInfoView.as_view(), name="backend-announcement-info"),
    # 公告排序
    path('announcement/order/', views.AnnouncementOrderView.as_view(), name="backend-announcement-order"),
]

