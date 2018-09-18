# -*- coding: UTF-8 -*-
from django.urls import path
from . import views
from . import views_pk

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
    # 玩法规则图
    path('guess/play_rule/', views.PlayRuleImage.as_view(), name="app-v1-guess-play_rule"),

    # ========== 股指pk ==========
    # 竞猜详情
    path('stock_pk_detail/', views_pk.StockPkDetail.as_view(), name="app-stock_pk-stock_pk_detail"),
    # 开奖记录
    path('stock_pk_results/list/', views_pk.StockPkResultList.as_view(), name="app-stock_pk-result_list"),
    # 竞猜记录
    path('stock_pk_records/list/', views_pk.StockPkRecordsList.as_view(), name="app-stock_pk-records_list"),
    # 下注
    path('stock_pk_bet/', views_pk.StockPkBet.as_view(), name="app-stock_pk-bet"),
]
