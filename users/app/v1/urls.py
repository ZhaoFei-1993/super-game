# -*- coding: UTF-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    # 用户信息        已测试
    path('info/<int:roomquiz_id>/', views.InfoView.as_view(), name="app-v1-user-info"),
    # 首页推送
    path('quiz_push/', views.QuizPushView.as_view(), name="app-v1-user-quiz_push"),
    # 注册,登录接口        已测试
    path('login/', views.LoginView.as_view(), name="app-v1-user-login"),
    # 忘记密码        已测试
    path('forgetpassword/', views.ForgetPasswordView.as_view(), name="app-v1-forget_password"),
    # 修改密码        已测试
    path('change/password/', views.ChangePasswordView.as_view(), name="app-v1-change-password"),
    # 邀请码校验
    path('invitation_code/check/', views.CheckInvitationCode.as_view(), name="app-v1-invitation-code-check"),
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
    path('message/list/<int:type>/', views.MessageListView.as_view(), name="app-v1-user-message"),
    # 获取消息详细内容
    path('detail/<int:user_message_id>/', views.DetailView.as_view(), name="app-v1-user-detail"),
    # 一键阅读所有消息公告
    path('message/all-read/', views.AllreadView.as_view(), name="app-v1-user-all-read"),
    # 钱包
    path('asset/', views.AssetView.as_view(), name="app-v1-user-asset"),
    # 提交提现申请
    path('asset/presentation/', views.UserPresentationView.as_view(), name="app-v1-user-asset-presentation"),
    # 提现记录表
    path('asset/list_pre/<int:c_id>/', views.PresentationListView.as_view(), name='app-v1-user-asset-list_pre'),
    # 提现记录表明细
    path('asset/list_pre/<int:coin_id>/<int:p_id>/', views.PresentationDetailView.as_view(),
         name='app-v1-user-asset-list_pre-detail'),
    # 充值记录表
    path('asset/list_recharge/<int:coin_id>/', views.RechargeListView.as_view(),
         name='app-v1-user-asset-list_recharge'),
    # 充值记录表明细
    path('asset/list_recharge/<int:coin_id>/<int:r_id>/', views.RechargeDetailView.as_view(),
         name='app-v1-user-asset-list_recharge-detail'),
    # 用户GSG锁定
    path('asset/lock/', views.AssetLock.as_view(), name='app-v1-user-asset-lock'),
    # 用户GSG锁定记录列表
    path('asset/lock_list/', views.LockListView.as_view(), name='app-v1-user-asset-lock_list'),
    # 用户GSG锁定记录详情及延长锁定设置
    path('asset/lock_list/<int:id>/', views.LockDetailView.as_view(), name='app-v1-user-asset-lock_detail'),
    # 用户设置其他(index支持1-5)
    path('setting_others/<int:index>/', views.SettingOthersView.as_view(), name='app-v1-user-setting_others'),
    # 用户币种充值和提现操作记录
    path('asset/coin_operate/<int:coin>/', views.CoinOperateView.as_view(), name='app-v1-usre-asset-coin_operate'),
    # 操作记录明细
    path('asset/coin_operate/<int:coin>/<int:pk>/', views.CoinOperateDetailView.as_view(),
         name='app-v1-user-asset-coin_operate-detail'),
    # 安卓版本控制
    path('android/version/', views.VersionUpdateView.as_view(), name='app-v1-user-android-version'),
    # 更换头像
    path('image/head/', views.ImageUpdateView.as_view(), name='app-v1-user-head'),
    # 抽奖列表
    path('luck_draw_list/', views.LuckDrawListView.as_view(), name="app-v1-user-luck-draw-list"),
    # 点击抽奖
    path('click_luck_draw/', views.ClickLuckDrawView.as_view(), name="app-v1-user-click_luck_draw"),
    # 活动图片
    path('activity_image/', views.ActivityImageView.as_view(), name="app-v1-user-activity_image"),
    # usdt活动图片
    path('usdt_act_image/', views.USDTActivityView.as_view(), name="app-v1-user-usdt_act_image"),
    # 电话区号列表
    path('countries/', views.CountriesView.as_view(), name="app-v1-user-countries"),
    # 首页推送
    path('home/message/', views.HomeMessageView.as_view(), name='app-v1-user-message-home'),
    # 分红记录
    path('dividend/<int:lock_id>/', views.DividendHistory.as_view(), name='app-v1-user-dividend-lock'),
    # soc 活动图片生成
    path('soc_activity/', views.Url_list.as_view(), name='app-v1-user-soc-activity'),

    # 扫码注册接口
    path('invitation/register/', views.InvitationRegisterView.as_view(), name="app-v1-user-invitation-register"),
    # 用户邀请信息界面
    path('invitation/info/', views.InvitationInfoView.as_view(), name="app-v1-user-invitation-register"),
    # 扫码拿用户消息
    path('invitation/user/', views.InvitationUserView.as_view(), name="app-v1-user-invitation-register"),
    # 生成带二维码邀请海报
    path('invitation/qr_merge/', views.InvitationMergeView.as_view(), name="app-v1-user-invitation-qr-merge"),

    #  转账:余额信息
    path('move/coin/', views.MoveCoinView.as_view(), name="move_coin"),
    # 转账:收款人信息
    path('move/recipient/', views.MoveRecipientView.as_view(), name="move_recipient"),
    #  点击转账
    path('move/finish/', views.MoveFilishView.as_view(), name="move_finish"),
    # 转账记录
    path('move/record/', views.MoveRecordView.as_view(), name="move_record"),

    # # get:币种切换列表   post：币种切换
    # path('coin/type/<int:index>/', views.CoinTypeView.as_view(), name='app-v1-user-coin-type'),
    # # 资产锁定
    # path('asset/lock/', views.AssetLockView.as_view(), name="app-v1-user-asset-lock"),
    # # ETH提现审核
    # path('asset/review/<int:c_id>/', views.ReviewListView.as_view(), name='app-v1-user-asset-review'),
    # # GGTC锁定记录
    # path('asset/lock_list/', views.LockListView.as_view(), name='app-v1-user-asset-lock_list'),
    # # GGTC分红表
    # path('asset/dividend/', views.DividendView.as_view(), name='app-v1-user-asset-dividend'),
    # 用户充值
    # path('recharge/<int:index>/', views.UserRechargeView.as_view(), name='app-v1-user-recharge'),

    # 投注返现记录
    path('cash_back/record/', views.CashBackRecord.as_view(), name="cash_back_record"),
]
