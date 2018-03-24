# -*- coding: UTF-8 -*-
from django.urls import path

from . import views
from utils import views as utils_views

urlpatterns = [
    path('login/', utils_views.ObtainAuthToken.as_view(), name="backend-login"),
    path('role/', views.RoleListView.as_view(), name="backend-admin-role-list"),
    path('profile/', views.InfoView.as_view(), name="backend-profile"),
    path('quiz/', views.QuizView.as_view(), name="backend-admin-quiz"),
]
