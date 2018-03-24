# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('sitemap/', views.sitemap, name="backend-admin-sitemap"),
    path('captcha/', views.captcha_generate, name="backend-captcha"),
    path('captcha/', views.sidebar_control, name="backend-sidebar-control"),
    path('upload/', views.upload, name="backend-upload"),
]
