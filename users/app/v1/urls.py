# -*- coding: UTF-8 -*-
from django.urls import path

from . import views

urlpatterns = [
    # 用户信息        已测试
    path('info/', views.InfoView.as_view(), name="app-v1-user-info"),
    # 注册,登录接口        已测试
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
    #  修改用户昵称
    path('nickname/', views.NicknameView.as_view(), name="app-v1-user-nickname"),
    # 手机号绑定
    path('telephone/bind/', views.BindTelephoneView.as_view(), name="app-v1-user-telephone-bind"),
    # 解除手机绑定
    path('telephone/unbind/', views.UnbindTelephoneView.as_view(), name="app-v1-user-telephone-unbind"),
    # 排行榜       已经测试
    path('ranking/', views.RankingView.as_view(), name="app-v1-user-ranking"),
    # 用户退出登录           未测试
    path('logout/', views.LogoutView.as_view(), name="app-v1-user-logout"),
    # 密保设置           已测试
    path('passcode/', views.PasscodeView.as_view(), name="app-v1-user-passcode"),
    # 原密保校验       已测试
    path('passcode/check/', views.ForgetPasscodeView.as_view(), name="app-v1-user-passcode-check"),
    # 忘记密保             已测试
    path('passcode/back/', views.BackPasscodeView.as_view(), name="app-v1-user-back-passcode"),
    # 音效/消息免推送 开关     已测试
    path('switch/', views.SwitchView.as_view(), name="app-v1-user-switch"),
    #  签到列表
    path('daily/list/', views.DailyListView.as_view(), name="app-v1-user-daily"),
    # 点击签到
    path('daily/sign/', views.DailySignListView.as_view(), name="app-v1-user-daily-sign"),
    #  通知列表
    path('message/<int:type>/', views.MessageView.as_view(), name="app-v1-user-message"),
    # 阅读，一键阅读
    path('read/', views.ReadView.as_view(), name="app-v1-user-read"),
]

