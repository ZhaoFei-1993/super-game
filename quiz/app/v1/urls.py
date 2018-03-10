# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    #  竞猜分类
    path('category/', views.CategoryView.as_view(), name="app-v1-quiz-category"),
    #  热门比赛
    path('hotest/', views.HotestView.as_view(), name="app-v1-quiz-hotest"),
    # 竞猜列表
    path('list/', views.QuizListView.as_view(), name="app-v1-quiz-list"),
]

