# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('list/', views.ListView.as_view(), name="app-v1-user-list"),
    path('info/', views.InfoView.as_view(), name="app-v1-user-info"),
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
]

