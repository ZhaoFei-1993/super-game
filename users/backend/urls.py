from django.urls import path

from . import views

urlpatterns = [
    # 锁定周期管理
    # path('coin/lock/', views.CoinLockListView.as_view(), name="backend-coin-lock"),
    # path('coin/lock/<int:pk>/', views.CoinLockDetailView.as_view(), name="coinlock-detail"),
    # 币种管理
    path('currency/', views.CurrencyListView.as_view(), name="backend-coin-currency"),
    path('currency/<int:pk>/', views.CurrencyDetailView.as_view(), name="coin-detail"),
    #  登录
    path('login/', views.LoginView.as_view(), name="backend-login"),
    #  锁定列表
    path('user/lock/', views.UserLockListView.as_view(), name="backend-user-lock"),
    # 用户资产管理
    path('user/coin/', views.UserCoinListView.as_view(), name="backend-user-coin"),
    # 用户列表
    path('users/', views.UserListView.as_view(), name="backend-user-list"),
    path('users/<int:pk>/', views.UserListDetailView.as_view(), name="user-detail"),
    # 用户资产明细
    path('coin/detail/', views.CoinDetailView.as_view(), name="coin-detail"),
    # 用户列表
    path('user_all/', views.UserAllView.as_view(), name="backend-user-all"),
    # 推荐人信息
    path('user_all/<int:pk>/', views.UserAllDetailView.as_view(), name="backend-user-all-detail"),
    # Ip同列表
    path('user_all/ip/<int:id>/', views.SameIPAddressView.as_view(), name="backend-user-all-detail"),
    # 邀请好友数
    path('invite_new/<int:pk>/', views.InviteNewView.as_view(), name="backend-invite_new"),
    # 提现列表
    path('coin_present/', views.CoinPresentView.as_view(), name="backend-present"),
    # 提现审核
    path('coin_present_check/<int:pk>/', views.CoinPresentCheckView.as_view(), name="backend-present_check"),
    # 充值记录
    path('recharge_list/<int:pk>/<coin_name>/', views.RechargeView.as_view(), name="backend-recharge"),
    # 充值记录(全部)
    path('recharge_all/', views.RechargeAllView.as_view(), name="backend-recharge_all"),
    # 积分(GSG)记录
    path('gsg_backend_list/<int:pk>/', views.GSGBackendView.as_view(), name="backend-gsg_backend_list"),
    # 资金明细
    path('coin_backend_detail/<int:pk>/', views.CoinBackendDetail.as_view(), name="backend-coin_backend_detail"),
    # 系统奖励及其他
    path('backend_coin_reward/<int:pk>/<coin_name>/', views.RewardBackendDetail.as_view(),
         name="backend-backend_coin_reward"),
    # 用户提现列表
    path('coin_present/<int:pk>/<int:coin>/', views.CoinPresentDetailView.as_view(), name="backend-present-detail"),
    # 运营数据
    path('run_data/', views.RunningView.as_view(), name='backend-run_data'),
    # 用户统计
    path('user_sts/', views.UserSts.as_view(), name='user-backend-user_sts'),
    # 币种统计
    path('coin_sts/<int:club_room>/', views.CoinSts.as_view(), name='user-backend-coin_sts'),
    # 登录统计
    path('login_rate/', views.LoginRateView.as_view(), name='user-backend-login_rate'),
    # 留存率统计
    path('remain_rate/', views.RemainRate.as_view(), name='user-backend-remain_rate'),
    # 俱乐部统计
    path('run_data/club_sts/<int:r_id>/', views.ClubSts.as_view(), name='user-backend-run_data-clubsts'),
    # gsg统计
    path('gsg_sts/', views.GSGStsView.as_view(), name='user-backend-gsg_sts'),
    # test
    # path('jjtest/', views.JJtest.as_view(), name='user-backend-test')
    path('ip_first/<int:user_id>/', views.IpLoginView.as_view(), name='user-backend-ip_first')
]
