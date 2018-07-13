# -*- coding: UTF-8 -*-
from django.db import models
import datetime
import reversion


@reversion.register()
class Image(models.Model):
    path = "./images/" + datetime.datetime.now().strftime('%Y%m%d')

    image = models.ImageField(upload_to=path)


# Create your models here.
@reversion.register()
class CodeModel(models.Model):
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    name = models.CharField(verbose_name="图片名称", max_length=100)
    position = models.CharField(verbose_name="正确坐标", max_length=100)
    count = models.SmallIntegerField(verbose_name="验证次数", default=0)  # 超过三次无法继续验证
    key = models.CharField(verbose_name="校验值", max_length=100)
    status = models.BooleanField(verbose_name="校验状态",default=0) # 0 未校验，1已校验
    is_delete = models.BooleanField(verbose_name="是否删除",default=0) # 0未删除 1删除

    class Meta:
        ordering = ['id']
        verbose_name = verbose_name_plural = "验证码表"
