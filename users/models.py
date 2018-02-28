# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin


class UserManager(BaseUserManager):
    """
    用户操作
    """


class User(AbstractBaseUser):
    username = models.CharField(verbose_name="用户账号", max_length=32)
    nickname = models.CharField(verbose_name="用户昵称", max_length=20)
    avatar = models.CharField(verbose_name="头像", max_length=255, default='')
    telephone = models.CharField(verbose_name="手机号码", max_length=11)
    pass_code = models.CharField(verbose_name="资金密保", max_length=32)
    eth_address = models.CharField(verbose_name="ETH地址", max_length=32)
    meth = models.IntegerField(verbose_name="METH余额", default=0)
    ggtc = models.IntegerField(verbose_name="GGTC余额", default=0)
    is_sound = models.BooleanField(verbose_name="是否开启音效", default=False)
    is_notify = models.BooleanField(verbose_name="是否开启推送", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class Coin(models.Model):
    EMTH = 1
    ETH = 2
    TYPE_CHOICE = (
        (EMTH, "EMTH"),
        (ETH, "ETH"),
    )
    icon = models.CharField(verbose_name="货币图标", max_length=255)
    name = models.CharField(verbose_name="货币名称", max_length=255)
    type = models.CharField(verbose_name="货币类型", choices=TYPE_CHOICE, max_length=1, default=EMTH)
    exchange_rate = models.IntegerField(verbose_name="兑换比例，当type值为2（ETH）时", default=0)
    is_lock = models.BooleanField(verbose_name="是否锁定", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币种类表"


class CoinLock(models.Model):
    period = models.IntegerField(verbose_name="锁定周期", default=0)
    profit = models.DecimalField(verbose_name="收益率", max_digits=10, decimal_places=3, default=0.000)
    limit_start = models.IntegerField(verbose_name="锁定起步金额", default=0)
    limit_end = models.IntegerField(verbose_name="最大锁定金额", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "代币锁定配置"


class CoinLockRelation(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    coin_lock = models.ForeignKey(CoinLock, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币与货币锁定周期关联表"

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
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户签到记录表"
