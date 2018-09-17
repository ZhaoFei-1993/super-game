# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 用户邀请信息界面
    path('promotion/info/', views.PromotionInfoView.as_view(), name="promotion-user-invitation-register"),
    ## 扫描二维码拿用户消息
    # path('promotion/user/', views.PromotionUserView.as_view(), name="promotion-user-invitation-register"),
    ## 用户生成带二维码邀请界面
    # path('promotion/qr_merge/', views.PromotionMergeView.as_view(), name="promotion-user-invitation-qr-merge"),
]
