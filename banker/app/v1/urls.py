# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 联合坐庄：   首页
    path('banker/home/', views.BankerHomeView.as_view(), name="banker_home"),
    # 联合坐庄：  详情
    path('banker/info/', views.BankerInfoView.as_view(), name='banker_info'),
    # 联合坐庄：  认购信息
    path('banker/details/', views.BankerDetailsView.as_view(), name='banker_details'),
    # 联合坐庄：  点击认购
    path('banker/buy/', views.BankerBuyView.as_view(), name='banker_buy'),
    # 联合坐庄：   投注记录
    path('banker/record/', views.BankerRecordView.as_view(), name='banker_record'),
    #  记录下俱乐部
    path('banker/club/', views.BankerClubView.as_view(), name="record-banker-club"),
    #  投注流水
    path('banker/amount_details/', views.AmountDetailsView.as_view(), name="record-banker-amount-details"),

]
