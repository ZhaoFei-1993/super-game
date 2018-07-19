# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 股票列表
    path('stock/list/', views.StockList.as_view(), name="app-v1-stock-list"),
]
