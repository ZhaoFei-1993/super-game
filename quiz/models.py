# -*- coding: UTF-8 -*-
from django.db import models
from wc_auth.models import Admin
from django.template.backends import django
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin


class Category(models.Model):
    name = models.CharField(verbose_name="分类名称", max_length=50)
    lft = models.IntegerField(verbose_name="奖励数", default=0)
    right = models.IntegerField(verbose_name="奖励数", default=0)
    # tree_id = models.IntegerField(verbose_name="奖励数", default=0)
    mptt_level = models.IntegerField(verbose_name="奖励数", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, default=0)
    # parent_id = models.IntegerField(verbose_name="奖励数", default=0)
    order = models.IntegerField(verbose_name="奖励数", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜分类表"


class Quiz(models.Model):
    category = models.ForeignKey(Category, verbose_name="竞猜分类", on_delete=models.DO_NOTHING)
    host_team = models.CharField(verbose_name="主队", max_length=255)
    guest_team = models.CharField(verbose_name="客队", max_length=255)
    begin_at = models.DateTimeField(verbose_name="比赛开始时间")
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜表"


class QuizCoin(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜所支持的货币种类"

# class QuizRule(models.Model):
#     quiz_id = models.ForeignKey(Quiz, on_delete=models.CASCADE)
# type =
