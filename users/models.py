# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)


class UserManager(BaseUserManager):
    """
    用户操作
    """


class User(AbstractBaseUser):
    username = models.CharField(verbose_name="用户账号", max_length=32)
    nickname = models.CharField(verbose_name="用户昵称", max_length=20)
    telephone = models.CharField(verbose_name="手机号码", max_length=11)
    pass_code = models.CharField(verbose_name="资金密保", max_length=32)
    eth_address = models.CharField(verbose_name="ETH地址", max_length=32)
    meth = models.IntegerField(verbose_name="METH余额")
    ggtc = models.IntegerField(verbose_name="GGTC余额")
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
