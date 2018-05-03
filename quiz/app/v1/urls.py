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
    # 我的竞猜记录             ***
    path('records/<int:roomquiz_id>/', views.RecordsListView.as_view(), name="app-v1-quiz-records"),
    # 他人的竞猜记录
    path('records/', views.RecordsListView.as_view(), name="app-v1-quiz-records"),
    # 竞猜详情
    path('<int:quiz_id>/', views.QuizDetailView.as_view(), name="app-v1-quiz-detail"),
    # 竞猜详情页面推送
    path('quiz_push/<int:quiz_id>/', views.QuizPushView.as_view(), name="app-v1-quiz-push"),
    # 竞猜选项
    path('rule/<int:quiz_id>/', views.RuleView.as_view(), name="app-v1-quiz-rule"),
    # 竞猜下注
    path('bet/', views.BetView.as_view(), name="app-v1-quiz-bet"),
    # 竞猜推荐
    path('recommend/', views.RecommendView.as_view(), name="app-v1-quiz-recommend")

]
