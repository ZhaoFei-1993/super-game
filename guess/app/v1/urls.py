# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 股票列表
    path('stock/list/', views.StockList.as_view(), name="app-v1-stock-list"),
    # 详情页面推送
    path('guess/', views.GuessPushView.as_view(), name="app-v1-guess-push"),
    # 股票选项
    path('play/<int:quiz_id>/', views.PlayView.as_view(), name="app-v1-quiz-rule"),
]
