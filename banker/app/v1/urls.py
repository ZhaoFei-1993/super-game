# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 联合坐庄：   首页
    path('banker/home/', views.BankerHomeView.as_view(), name="banker_home"),
    # 联合坐庄：  详情
    path('banker/info/', views.BankerInfoView.as_view(), name='banker_info'),
    # 联合坐庄：   坐庄
    # path('banker/detail/', views.BankerDetailView.as_view(), name='banker_detail'),

]
