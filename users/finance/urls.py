from django.urls import path

from . import views

urlpatterns = [
    # 登陆
    path('login/', views.LoginView.as_view(), name="finance-user-login"),
    # 修改密码
    path('password/', views.PwdView.as_view(), name="finance-user-password"),
    # 平台统计,type:club or game
    path('count/<str:type>/<int:pk>/', views.CountView.as_view(),name='finance-user-count'),
    # 日期统计
    path('date/count/<str:type>/<int:pk>/', views.DateCountView.as_view(),name='finance-user-datecount'),
    # 盈利统计
    path('bet/count/<str:type>/<int:pk>/',views.BetCountView.as_view(),name = 'finance-user_bet'),
    # 获取当前用户系统消息,无表，pass
    path('public_massage/',views.MassageView.as_view(),name='finance-user-message'),
    # 获取后台消息表详情
    path('public_massage_detail/<int:message_id>/',views.MessageDetailView.as_view(),name='finance-user-message_detail'),
    # GSG运营平台
    path('GSG/',views.GSGView.as_view(),name='finance-user-gsg'),
    # 股份配置
    path('shares/',views.SharesView.as_view(),name='finance-user-shares'),
    # ICO/基石
    path('footstone/',views.FootstoneView.as_view(),name='finance-user-footstone'),
    # 俱乐部列表
    path('club/',views.ClubView.as_view(),name='finance-user-club'),
    # 游戏列表
    path('game/',views.GameView.as_view(),name='finance-user-game'),
    # 提现列表
    path('present/', views.PresentView.as_view(), name='finance-user-present'),
    # 提现审核操作
    path('present/<int:pk>/', views.PresentDetailView.as_view(), name='finance-user-present'),
    # 财务报表
    path('finance/',views.FinanceView.as_view(),name='finance-user-finance'),
    # 提现打款操作
    path('bill/<int:pk>/', views.BillView.as_view(), name= 'finance-user-bill'),
    # 玩法列表
    path('playlist/', views.PlayListView.as_view(), name='finance-user-playlist'),
    # 玩法详情
    path('playlist/<int:play_id>/', views.PlayDetailView.as_view(), name='finance-user-playdetail')
]