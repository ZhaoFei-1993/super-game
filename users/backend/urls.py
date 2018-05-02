from django.urls import path

from . import views

urlpatterns = [
    # 锁定周期管理
    path('coin/lock/', views.CoinLockListView.as_view(), name="backend-coin-lock"),
    path('coin/lock/<int:pk>/', views.CoinLockDetailView.as_view(), name="coinlock-detail"),
    # 币种管理
    path('currency/', views.CurrencyListView.as_view(), name="backend-coin-currency"),
    path('currency/<int:pk>/', views.CurrencyDetailView.as_view(), name="coin-detail"),
    #  登录
    path('login/', views.LoginView.as_view(), name="backend-login"),
    #  锁定列表
    path('user/lock/', views.UserLockListView.as_view(), name="backend-user-lock"),
    # 用户资产管理
    path('user/coin/', views.UserCoinListView.as_view(), name="backend-user-coin"),
    # 用户列表
    path('users/', views.UserListView.as_view(), name="backend-user-list"),
    path('users/<int:pk>/', views.UserListDetailView.as_view(), name="user-detail"),
    #用户资产明细
    path('coin/detail/', views.CoinDetailView.as_view(), name="coin-detail"),
    #用户允许投注值及兑换积分
    path('coin/reward_value/', views.CoinRewardAndValueView.as_view(),name ="coin-reward-value")
]
