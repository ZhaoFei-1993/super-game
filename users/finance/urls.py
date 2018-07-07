from django.urls import path

from . import views

urlpatterns = [
    # 登陆
    path('login/', views.LoginView.as_view(), name="finance-user-login"),
    # 修改密码
    path('password/', views.PwdView.as_view(), name="finance-user-password"),
    # 平台统计,type:club or game
    path('count/<str:type>/<int:pk>/<str:cycle>/', views.CountView.as_view(),name='finance-user-count'),
    # 获取当前用户系统消息,无表，pass
    path('public_massage/',views.MassageView.as_view(),name='finance-user-message'),
    # 获取后台消息表详情
    path('public_massage_detail/<int:message_id>/',views.MessageDetailView.as_view(),name='finance-user-message_detail'),
    # GSG运营平台
    path('GSG/',views.GSGView.as_view(),name='finance-user-gsg')
]