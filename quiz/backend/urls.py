# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name="quiz-category-list"),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name="quiz-category-detail"),
    path('quizs/', views.QuizListView.as_view(), name="quiz-list"),
    path('user_quiz/', views.UserQuizView.as_view(), name="quiz-user_quiz"),
]

