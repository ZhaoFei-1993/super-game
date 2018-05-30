# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name="quiz-category-list"),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name="quiz-category-detail"),
    path('quizs/', views.QuizListView.as_view(), name="quiz-list"),
    path('user_quiz/', views.UserQuizView.as_view(), name="quiz-user_quiz"),
    path('quiz_list_backend/<int:category>/', views.QuizListBackEndView.as_view(), name='quiz_list_backend'),
    path('quiz_list_backend/<int:quiz_id>/<int:room>/<int:type>/', views.QuizListBackEndDetailView.as_view(), name='quiz_list_backend_detail'),
    path('quiz_user_list/<int:user_id>/',views.UserQuizListView.as_view(), name='quiz_user_list'),
]
