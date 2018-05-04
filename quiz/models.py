# -*- coding: UTF-8 -*-
from django.db import models
from wc_auth.models import Admin
from django.template.backends import django
from mptt.models import MPTTModel, TreeForeignKey
from users.models import Coin, User
import reversion


@reversion.register()
class Category(MPTTModel):
    name = models.CharField(verbose_name="分类名称", max_length=50)
    icon = models.CharField(verbose_name="分类图标", max_length=255, default='')
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='自身ID', db_index=True, on_delete=models.CASCADE)
    order = models.IntegerField(verbose_name="排序", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜分类表"


@reversion.register()
class Quiz(models.Model):
    PUBLISHING = 0  # 已发布
    REPEALED = 1  # 比赛中
    ENDED = 2  # 已结束
    PUBLISHING_ANSWER = 3  # 已发布答案
    BONUS_DISTRIBUTION = 4  # 已分配奖金
    TITLE_FIRST_AUDIT = 11  # 题目初审
    TITLE_FINAL_AUDIT = 12  # 题目终审
    OPTION_FIRST_AUDIT = 13  # 答案初审
    OPTION_FINAL_AUDIT = 14  # 答案终审
    TITLE_FIRST_AUDIT_REJECT = 21  # 题目初审不通过
    TITLE_FINAL_AUDIT_REJECT = 22  # 题目终审不通过
    OPTION_FIRST_AUDIT_REJECT = 23  # 答案初审不通过
    OPTION_FINAL_AUDIT_REJECT = 24  # 答案终审不通过

    STATUS_CHOICE = (
        (PUBLISHING, "已发布"),
        (REPEALED, "比赛中"),
        (ENDED, "已结束"),
        (PUBLISHING_ANSWER, "已发布答案"),
        (BONUS_DISTRIBUTION, "已分配奖金"),
        (TITLE_FIRST_AUDIT, "题目初审"),
        (TITLE_FINAL_AUDIT, "题目终审"),
        (OPTION_FIRST_AUDIT, "答案初审"),
        (OPTION_FINAL_AUDIT, "答案终审"),
        (TITLE_FIRST_AUDIT_REJECT, "题目初审不通过"),
        (TITLE_FINAL_AUDIT_REJECT, "题目终审不通过"),
        (OPTION_FIRST_AUDIT_REJECT, "答案初审不通过"),
        (OPTION_FINAL_AUDIT_REJECT, "答案终审不通过"),
    )
    category = models.ForeignKey(Category, verbose_name="竞猜分类", on_delete=models.DO_NOTHING)
    host_team = models.CharField(verbose_name="主队", max_length=255)
    host_team_avatar = models.CharField(verbose_name="主队图标", max_length=255, default='')
    host_team_score = models.IntegerField(verbose_name="主队分数", default=0)
    guest_team = models.CharField(verbose_name="客队", max_length=255)
    guest_team_avatar = models.CharField(verbose_name="客队图标", max_length=255, default='')
    guest_team_score = models.IntegerField(verbose_name="客队分数", default=0)
    match_name = models.CharField(verbose_name="联赛名称", max_length=50, default="")
    status = models.CharField(verbose_name="状态", choices=STATUS_CHOICE, max_length=2, default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    total_people = models.IntegerField(verbose_name="总参与人数", default=0)
    begin_at = models.DateTimeField(verbose_name="比赛开始时间/截止日期")
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    match_flag = models.CharField(verbose_name='比赛标识', null=True, max_length=16, default='')

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜表"


@reversion.register()
class QuizCoin(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜所支持的货币种类"


@reversion.register()
class Rule(models.Model):
    RESULTS = 0
    POLITENESS_RESULTS = 1
    SCORE = 2
    TOTAL_GOAL = 3
    RESULT = 4
    POLITENESS_RESULT = 5
    SIZE_POINTS = 6
    VICTORY_GAP = 7
    TYPE_CHOICE = (
        (RESULTS, "赛果"),
        (POLITENESS_RESULTS, "让分赛果"),
        (SCORE, "比分"),
        (TOTAL_GOAL, "总进球"),
        (RESULT, "胜负"),
        (POLITENESS_RESULT, "让分胜负"),
        (SIZE_POINTS, "大小分"),
        (VICTORY_GAP, "胜分差"),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    type = models.CharField(verbose_name="玩法", choices=TYPE_CHOICE, max_length=1, default=RESULTS)
    tips = models.CharField(max_length=100, verbose_name="选项说明", default="")
    home_let_score = models.DecimalField(verbose_name="主队让分，让分赛果，让分胜负玩法适用", max_digits=10, decimal_places=2,
                                         default=0.00)
    guest_let_score = models.DecimalField(verbose_name="客队让分，让分赛果，让分胜负玩法适用", max_digits=10, decimal_places=2,
                                          default=0.00)
    estimate_score = models.DecimalField(verbose_name="预估分数，大小分玩法适用", max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜规则表"


@reversion.register()
class Option(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.CharField(verbose_name="选项值", max_length=20, default="")
    option_type = models.CharField(verbose_name="选项分类", max_length=20, default="")
    order = models.IntegerField(verbose_name="排序", default=0)
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2, default=0.00)
    is_right = models.BooleanField(verbose_name="是否正确选项", default=False)
    flag = models.CharField(verbose_name='开奖标记', max_length=8, default="")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "竞猜选项表"


@reversion.register()
class Record(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    roomquiz_id = models.IntegerField(verbose_name="俱乐部题目ID", default=0)
    # bet = models.IntegerField(verbose_name="下注金额", default=0)
    bet = models.DecimalField(verbose_name="下注金额", max_digits=10, decimal_places=1, default=0.0)
    earn_coin = models.IntegerField(verbose_name="获得猜币数", default=0)
    created_at = models.DateTimeField(verbose_name="下注时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户下注表"
