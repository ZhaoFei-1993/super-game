# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin
import reversion


class UserManager(BaseUserManager):
    """
    用户操作
    """


@reversion.register()
class User(AbstractBaseUser):
    WECHAT = 1
    IOS = 2
    ANDROID = 3
    HTML5 = 4
    ROBOT = 5

    REGISTER_QQ = 1
    REGISTER_WECHAT = 2
    REGISTER_TELEPHONE = 3
    REGISTER_UNKNOWN = 4
    REGISTER_CONSOLE = 5

    DISABLE = 0
    ENABLE = 1
    DELETE = 2

    USER_STATUS = (
        (DISABLE, "用户禁用"),
        (ENABLE, "用户启用"),
        (DELETE, "用户删除")
    )

    SOURCE_CHOICE = (
        (WECHAT, "微信用户"),
        (IOS, "iOS"),
        (ANDROID, "Android"),
        (HTML5, "HTML5"),
        (ROBOT, "机器人"),
    )
    REGISTER_TYPE = (
        (REGISTER_WECHAT, "微信登录"),
        (REGISTER_QQ, "QQ登录"),
        (REGISTER_TELEPHONE, "手机号码登录"),
        (REGISTER_UNKNOWN, "未知登录类型"),
        (REGISTER_CONSOLE, "系统注册"),
    )
    username = models.CharField(verbose_name="用户账号", max_length=32)
    nickname = models.CharField(verbose_name="用户昵称", max_length=20)
    register_type = models.CharField(verbose_name="注册类型", choices=REGISTER_TYPE, max_length=1, default=REGISTER_UNKNOWN)
    source = models.CharField(verbose_name="用户来源", choices=SOURCE_CHOICE, max_length=1, default=IOS)
    avatar = models.CharField(verbose_name="头像", max_length=255, default='')
    telephone = models.CharField(verbose_name="手机号码", max_length=11, default='')
    pass_code = models.CharField(verbose_name="资金密保", max_length=32, default='')
    is_sound = models.BooleanField(verbose_name="是否开启音效", default=False)
    is_notify = models.BooleanField(verbose_name="是否开启推送", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)
    status = models.CharField(verbose_name="用户状态", choices=USER_STATUS, max_length=1, default=ENABLE)
    integral = models.IntegerField(verbose_name='积分', default=0)
    is_robot = models.BooleanField(verbose_name="是否机器人", default=False)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username


# @reversion.register()
# class RewardCoin(models.Model):
#
#     created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
#
#     class Meta:
#         ordering = ['-id']
#         verbose_name = verbose_name_plural = "用户邀请表"


@reversion.register()
class Coin(models.Model):
    # GGTC = 1
    # ETH = 2
    # BTC = 3
    # LTC = 4
    # TYPE_CHOICE = (
    #     (GGTC, "GGTC"),
    #     (ETH, "METH"),
    #     (BTC, "MBTC"),
    #     (LTC, "MLTC"),
    # )
    icon = models.CharField(verbose_name="货币图标", max_length=255)
    name = models.CharField(verbose_name="货币名称", max_length=255)
    raw_name = models.CharField(verbose_name="货币充值前名称", max_length=255, default="")
    # type = models.CharField(verbose_name="货币类型", choices=TYPE_CHOICE, max_length=1, default=ETH)
    exchange_rate = models.IntegerField(verbose_name="兑换比例", default=1)
    # service_charge = models.DecimalField(verbose_name='提现手续费',max_digits=10, decimal_places=1, default=0.000)
    cash_control = models.IntegerField(verbose_name="提现下限", default=0)
    # is_lock = models.BooleanField(verbose_name="是否容许锁定", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币种类表"


@reversion.register()
class RewardCoin(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    value_ratio = models.IntegerField(verbose_name="兑换多少积分", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "奖励兑换表"


@reversion.register()
class CoinValue(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    value_index = models.IntegerField(verbose_name='投注值序号', default=1)
    value = models.DecimalField(verbose_name="货币允许投注值", max_digits=10, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币投注值表"


@reversion.register()
class UserCoin(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(verbose_name="余额", max_digits=18, decimal_places=2, default=0.00)
    is_opt = models.BooleanField(verbose_name="是否选择", default=False)
    is_bet = models.BooleanField(verbose_name="是否为下注选择", default=False)
    address = models.CharField(verbose_name="充值地址", max_length=32, default='')

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户代币余额表"


@reversion.register()
class CoinDetail(models.Model):
    RECHARGE = 1
    REALISATION = 2
    BETS = 3
    ACTIVITY = 4
    OPEB_PRIZE = 5
    LOCK = 6
    OTHER = 7
    TYPE_CHOICE = (
        (RECHARGE, "充值"),
        (REALISATION, "提现"),
        (BETS, "下注"),
        (ACTIVITY, "活动"),
        (OPEB_PRIZE, "开奖"),
        (LOCK, "锁定"),
        (OTHER, "系统增加"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_name = models.CharField(verbose_name="货币名称", max_length=255, default='')
    amount = models.CharField(verbose_name="操作数额", max_length=255)
    rest = models.DecimalField(verbose_name="余额", max_digits=10, decimal_places=3, default=0.000)
    sources = models.CharField(verbose_name="资金流动类型", choices=TYPE_CHOICE, max_length=1, default=BETS)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="操作时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = verbose_name_plural = "用户资金明细"


@reversion.register()
class CoinLock(models.Model):
    period = models.IntegerField(verbose_name="锁定周期", default=0)
    profit = models.DecimalField(verbose_name="收益率", max_digits=10, decimal_places=2, default=0.000)
    limit_start = models.IntegerField(verbose_name="锁定起步金额", default=0)
    limit_end = models.IntegerField(verbose_name="最大锁定金额", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    Coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "代币锁定配置"


@reversion.register()
class UserCoinLock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_lock = models.ForeignKey(CoinLock, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name="锁定金额", default=0)
    end_time = models.DateTimeField(verbose_name="锁定结束时间", auto_now_add=True)
    is_free = models.BooleanField(verbose_name="是否已解锁", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户货币锁定记录表"


@reversion.register()
class DailySettings(models.Model):
    days = models.IntegerField(verbose_name="签到天数", default=1)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, default='')
    rewards = models.IntegerField(verbose_name="奖励数", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    days_delta = models.IntegerField(verbose_name="间隔天数", default=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "签到配置表"


@reversion.register()
class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.IntegerField(verbose_name="连续签到天数", default=0)
    sign_date = models.DateTimeField(verbose_name="签到时间")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户签到记录表"


@reversion.register()
class Message(models.Model):
    GLOBAL = 1
    PUBLIC = 2
    PRIVATE = 3
    TYPE_CHOICE = (
        (GLOBAL, "系统消息"),
        (PUBLIC, "公共消息"),
        (PRIVATE, "私信"),
    )
    type = models.CharField(verbose_name="消息类型", choices=TYPE_CHOICE, max_length=1, default=PUBLIC)
    title = models.CharField(verbose_name="消息标题", max_length=100, default="")
    content = models.CharField(verbose_name="消息内容", max_length=255, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "消息内容表"


@reversion.register()
class UserMessage(models.Model):
    UNREAD = 0
    READ = 1
    DELETE = 2
    TYPE_CHOICE = (
        (UNREAD, "未读"),
        (READ, "已读"),
        (DELETE, "删除"),
    )
    status = models.CharField(verbose_name="消息状态", choices=TYPE_CHOICE, max_length=1, default=UNREAD)
    user = models.ForeignKey(User, verbose_name="收件人ID", on_delete=models.CASCADE)
    message = models.ForeignKey(Message, verbose_name="消息内容表外键", on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户消息表"


@reversion.register()
class UserRecharge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="充值数量", max_digits=10, decimal_places=3, default=0.000)
    address = models.CharField(verbose_name="充值地址", max_length=255, default="")
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户充值记录"


@reversion.register()
class UserPresentation(models.Model):
    APPLICATION = 0
    ADOPT = 1
    REFUSE = 2

    TYPE_CHOICE = (
        (APPLICATION, "提现申请中"),
        (ADOPT, "提现成功"),
        (REFUSE, "提现失败"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="提现数量", max_digits=10, decimal_places=3, default=0.000)
    rest = models.DecimalField(verbose_name='剩余数量', max_digits=10, decimal_places=3, default=0.000)
    address = models.CharField(verbose_name="提现ETH地址", max_length=255, default="")
    address_name = models.CharField(verbose_name="提现地址名称", max_length=255, default="")
    status = models.CharField(verbose_name="消息类型", choices=TYPE_CHOICE, max_length=1, default=APPLICATION)
    feedback = models.CharField(verbose_name="拒绝提现理由", max_length=255, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户提现记录表"


@reversion.register()
class UserSettingOthors(models.Model):
    about = models.CharField(verbose_name="关于", max_length=150, default="")  # 序号2
    helps = models.TextField(verbose_name="帮助")  # 序号3
    reg_type = models.IntegerField(verbose_name="用户注册类型", default=1)
    sv_contractus = models.TextField(verbose_name="服务条款")  # 序号4
    pv_contractus = models.TextField(verbose_name="隐私条款")  # 序号5
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户设置其他"
