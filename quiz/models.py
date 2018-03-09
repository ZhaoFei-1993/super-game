# -*- coding: UTF-8 -*-
from django.db import models
from wc_auth.models import Admin
from django.template.backends import django
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin,User


class Category(MPTTModel):
    name = models.CharField(verbose_name="分类名称", max_length=50)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='自身ID', db_index=True, on_delete=models.CASCADE)
    order = models.IntegerField(verbose_name="排序", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜分类表"


class Quiz(models.Model):
    category = models.ForeignKey(Category, verbose_name="竞猜分类", on_delete=models.DO_NOTHING)
    host_team = models.CharField(verbose_name="主队", max_length=255)
    host_team_avatar = models.CharField(verbose_name="主队图标", max_length=255, default='')
    guest_team = models.CharField(verbose_name="客队", max_length=255)
    guest_team_avatar = models.CharField(verbose_name="客队图标", max_length=255, default='')
    match_name = models.CharField(verbose_name="联赛名称", max_length=50, default="")
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
    RESULTS = 1
    ONE_TWO = 2
    TOTAL = 3
    SCORE = 4
    NEXT_BALL = 5
    OUTCOME = 6
    MIXTURE = 7
    COMITY_BRANCH = 8
    KATSUTA = 9
    BRANCH_SIZE = 8
    TYPE_CHOICE = (
        (RESULTS, "赛果"),
        (ONE_TWO, "单双"),
        (TOTAL, "总进球"),
        (SCORE, "比分"),
        (NEXT_BALL, "下一进球"),
        (OUTCOME, "胜负"),
        (MIXTURE, "混合过关"),
        (COMITY_BRANCH, "让分胜负"),
        (KATSUTA, "胜分差"),
        (BRANCH_SIZE, "大小分"),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    type = models.CharField(verbose_name="玩法", choices=TYPE_CHOICE, max_length=1, default=RESULTS)
    tips = models.CharField(max_length=100, verbose_name="选项说明", default="")
    handicap_score = models.IntegerField(verbose_name="让分分数，让分胜负玩法适用", default=0)
    estimate_score = models.IntegerField(verbose_name="预估分数，大小分玩法适用", default=0)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜规则表"


class Option(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.CharField(verbose_name="选项值", max_length=20, default="")
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=0.00)
    is_right = models.BooleanField(verbose_name="是否正确选项", default=False)

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






