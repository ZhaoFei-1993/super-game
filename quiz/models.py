# -*- coding: UTF-8 -*-
from django.db import models
from wc_auth.models import Admin
from django.template.backends import django
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin,User


class Category(MPTTModel):
    name = models.CharField(verbose_name="分类名称", max_length=50)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True, on_delete=models.CASCADE)
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


class Rule(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    # type =
    tips = models.CharField(max_length=100, verbose_name="选项说明", default="")
    # handicap_score =
    # estimate_score =

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜规则表"


class Option(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.CharField(verbose_name="选项值", max_length=20, default="")
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜规则表"



class Record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    bet = models.IntegerField(verbose_name="下注金额", default=0)
    created_at = models.DateTimeField(verbose_name="下注时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户下注表"






