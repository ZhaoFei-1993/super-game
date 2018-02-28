# -*- coding: UTF-8 -*-
from django.db import models
from wc_auth.models import Admin
from django.template.backends import django
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin


class AndroidEdition(models.Model):
    FALSE = 0
    TRUE = 1

    TYPE_CHOICE = (
        (FALSE, "不强制更新"),
        (TRUE, "强制更新"),
    )
    version = models.CharField(verbose_name="版本号", max_length=20, default="")
    url = models.CharField(verbose_name="APK下载链接地址", max_length=255, default="")
    is_force = models.CharField(verbose_name="是否强制更新", choices=TYPE_CHOICE, max_length=1, default=FALSE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "安卓版本管理"


class SystemDeploy(models.Model):
    # 系统配置数据，这里需要初始化数据
    conflg = models.CharField(verbose_name="配置项key", max_length=50, default=0)
    value = models.TextField(verbose_name="配置项值")
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "系统配置表"

















