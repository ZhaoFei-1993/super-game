# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 股票列表
    path('stock/list/', views.StockList.as_view(), name="app-v1-stock-list"),
    # 期数列表
    path('stock/periods/', views.PeriodsList.as_view(), name="app-v1-periods-list"),
    # 详情页面推送
    path('guess/list/', views.GuessPushView.as_view(), name="app-v1-guess-push"),
    # 股票选项
    path('play/', views.PlayView.as_view(), name="app-v1-guess-play"),
    # 股票下注
    path('bet/', views.BetView.as_view(), name="app-v1-guess-bet"),
    # 竞猜记录
    path('records/', views.RecordsListView.as_view(), name="app-v1-guess-records"),
    # 曲线图(时)
    path('graph/time/', views.StockGraphListView.as_view(), name="app-v1-guess-graph-time"),
    # 曲线图(日)
    path('graph/day/', views.StockGraphDayListView.as_view(), name="app-v1-guess-graph-day"),
]
