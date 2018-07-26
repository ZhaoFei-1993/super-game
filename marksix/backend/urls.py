# -*- coding: UTF-8 -*-
from django.urls import path

from ..backend import views

urlpatterns = [
    # 玩法列表
    path('play_list/', views.PlaysBackendList.as_view(), name='marksix-backend-play_list'),
    # 玩法明细
    path('play_list/<int:pk>/', views.PlaysBackendDetail.as_view(), name='marksix-backend-play_detail'),
    # 选项列表
    path('option_list/', views.OptionsBackendList.as_view(), name='marksix-backend-option_list'),
    # 选项明细
    path('option_list/<int:pk>/', views.OptionsBackendDetail.as_view(), name='marksix-backend-option_detail'),
    # 返回玩法字典格式
    path('play_tiny_list/', views.PlayTinyView.as_view(), name='marksix-backend-play_tiny_list'),
    # 开奖结果
    path('open_price/', views.OpenPriceBackendList.as_view(), name='marksix-backend-open_price'),
    # 开奖明细
    path('open_price/<int:pk>/', views.OpenPriceBackendDetail.as_view(), name='marksix-backend-open_price'),
]
