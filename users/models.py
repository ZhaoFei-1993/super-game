# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin


class UserManager(BaseUserManager):
    """
    用户操作
    """


class User(AbstractBaseUser):
    WECHAT = 1
    IOS = 2
    ANDROID = 3

    REGISTER_QQ = 1
    REGISTER_WECHAT = 2
    REGISTER_TELEPHONE = 3
    REGISTER_UNKNOWN = 4

    SOURCE_CHOICE = (
        (WECHAT, "微信用户"),
        (IOS, "iOS"),
        (ANDROID, "Android"),
    )
    REGISTER_TYPE = (
        (REGISTER_WECHAT, "微信登录"),
        (REGISTER_QQ, "QQ登录"),
        (REGISTER_TELEPHONE, "手机号码登录"),
        (REGISTER_TELEPHONE, "未知登录类型"),
    )
    username = models.CharField(verbose_name="用户账号", max_length=32)
    nickname = models.CharField(verbose_name="用户昵称", max_length=20)
    register_type = models.CharField(verbose_name="注册类型", choices=REGISTER_TYPE, max_length=1, default=REGISTER_UNKNOWN)
    source = models.CharField(verbose_name="用户来源", choices=SOURCE_CHOICE, max_length=1, default=IOS)
    avatar = models.CharField(verbose_name="头像", max_length=255, default='')
    telephone = models.CharField(verbose_name="手机号码", max_length=11, default='')
    pass_code = models.CharField(verbose_name="资金密保", max_length=32, default='')
    eth_address = models.CharField(verbose_name="ETH地址", max_length=32)
    meth = models.IntegerField(verbose_name="METH余额", default=0)
    ggtc = models.IntegerField(verbose_name="GGTC余额", default=0)
    is_sound = models.BooleanField(verbose_name="是否开启音效", default=False)
    is_notify = models.BooleanField(verbose_name="是否开启推送", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)
    victory = models.DecimalField(verbose_name="竞猜胜率", max_digits=3, decimal_places=1, default=0.0)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class Coin(models.Model):
    GGTC = 1
    ETH = 2
    TYPE_CHOICE = (
        (GGTC, "GGTC"),
        (ETH, "ETH"),
    )
    icon = models.CharField(verbose_name="货币图标", max_length=255)
    name = models.CharField(verbose_name="货币名称", max_length=255)
    type = models.CharField(verbose_name="货币类型", choices=TYPE_CHOICE, max_length=1, default=GGTC)
    exchange_rate = models.IntegerField(verbose_name="兑换比例，当type值为2（ETH）时", default=0)
    is_lock = models.BooleanField(verbose_name="是否容许锁定", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币种类表"


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


class UserCoinLock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_lock = models.ForeignKey(CoinLock, on_delete=models.CASCADE)
    amount = models.IntegerField(verbose_name="锁定金额", default=0)
    end_time = models.DateTimeField(verbose_name="锁定结束时间", auto_now_add=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户货币锁定记录表"


class DailySettings(models.Model):
    days = models.IntegerField(verbose_name="签到天数", default=1)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    rewards = models.IntegerField(verbose_name="奖励数", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "签到配置表"


class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.IntegerField(verbose_name="连续签到天数", default=0)
    sign_date = models.IntegerField(verbose_name="签到日期")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户签到记录表"


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


class UserRecharge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="充值数量", max_digits=10, decimal_places=3, default=0.000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户充值记录"


class UserPresentation(models.Model):
    APPLICATION = 0
    ADOPT = 1
    REFUSE = 2

    TYPE_CHOICE = (
        (APPLICATION, "申请中"),
        (ADOPT, "已处理"),
        (REFUSE, "已拒绝"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="提现数量", max_digits=10, decimal_places=3, default=0.000)
    rest = models.DecimalField(verbose_name='剩余数量', max_digits=10, decimal_places=3, default=0.000)
    address = models.CharField(verbose_name="提现ETH地址", max_length=255, default="")
    status = models.CharField(verbose_name="消息类型", choices=TYPE_CHOICE, max_length=1, default=APPLICATION)
    feedback = models.CharField(verbose_name="拒绝提现理由", max_length=255, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户提现记录表"


class UserSettingOthors(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    version = models.CharField(verbose_name="软件版本", max_length=20, default="")  # 序号1
    about = models.CharField(verbose_name="关于", max_length=150, default="")  # 序号2
    helps = models.TextField(verbose_name="帮助")  # 序号3
    sv_contractus = models.TextField(verbose_name="服务条款")  # 序号4
    pv_contractus = models.TextField(verbose_name="隐私条款")  # 序号5
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户设置其他"
