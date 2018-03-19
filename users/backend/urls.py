from django.urls import path

from . import views

urlpatterns = [
    path('coin/lock/', views.CoinLockListView.as_view(), name="backend-coin-lock"),
]
