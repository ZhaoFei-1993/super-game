from django.urls import path

from . import views

urlpatterns = [
    path('coin/lock/', views.CoinLockListView.as_view(), name="backend-coin-lock"),
    path('coin/lock/<int:pk>/', views.CoinLockDetailView.as_view(), name="coinlock-detail"),
    path('currency/', views.CurrencyListView.as_view(), name="backend-coin-currency"),
    path('currency/<int:pk>/', views.CurrencyDetailView.as_view(), name="coin-detail"),
    path('login/', views.LoginView.as_view(), name="backend-login"),
    path('user/lock/', views.UserLockListView.as_view(), name="backend-user-lock"),
]
