# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name="quiz-category-list"),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name="quiz-category-detail"),
    path('quizs/', views.QuizListView.as_view(), name="quiz-list"),
    path('user_quiz/', views.UserQuizView.as_view(), name="quiz-user_quiz"),
    #竞猜场次列表
    path('quiz_list_backend/<int:category>/', views.QuizListBackEndView.as_view(), name='quiz_list_backend'),
    #场次赛果情况
    path('quiz_detail_backend/<int:type>/', views.QuizListBackEndDetailView.as_view(), name='quiz_list_backend_detail'),
    #用户下注记录
    path('quiz_user_list/<int:user_id>/<int:room_id>/',views.UserQuizListView.as_view(), name='quiz_user_list'),
    #下注人数
    path('quiz_count_list/<int:room>/<int:pk>/', views.QuizCountListView.as_view(), name='quiz_count_list'),
]
