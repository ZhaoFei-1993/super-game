# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="backend-admin-login"),
]
