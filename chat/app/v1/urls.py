# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    #  创建俱乐部
    path('hotest/', views.QuizPushView.as_view(), name="app-v1-quiz-hotest"),
]

