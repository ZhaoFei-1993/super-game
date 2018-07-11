from django.db import models
import reversion
from users.models import User
from chat.models import Club


# Create your models here.
@reversion.register()
class Number(models.Model):
    ANIMAL_CHOICE = (
        (1, '鼠'),
        (2, '牛'),
        (3, '虎'),
        (4, '兔'),
        (5, '龙'),
        (6, '蛇'),
        (7, '马'),
        (8, '羊'),
        (9, '猴'),
        (10, '鸡'),
        (11, '狗'),
        (12, '猪'),
    )
    RED_WAVE = 1
    BLUE_WAVE = 2
    GREEN_WAVE = 3
    WAVE_CHOICE = (
        (RED_WAVE, '红波'),
        (BLUE_WAVE, '蓝波'),
        (GREEN_WAVE, '绿波')
    )

    ELEMENT_CHOICE = (
        (1, '金'),
        (2, '木'),
        (3, '水'),
        (4, '火'),
        (5, '土'),
    )
    num = models.SmallIntegerField(verbose_name="号码", null=False)
    animal = models.CharField(verbose_name="生肖", choices=ANIMAL_CHOICE, max_length=2)
    wave = models.CharField(verbose_name="波色", choices=WAVE_CHOICE, max_length=1)
    element = models.CharField(verbose_name="五行", choices=ELEMENT_CHOICE, max_length=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['num']
        verbose_name = verbose_name_plural = "六合彩号码表"


@reversion.register()
class Play(models.Model):
    title = models.CharField(verbose_name="玩法昵称", max_length=25)
    title_en = models.CharField(verbose_name="玩法昵称(en)", max_length=25, default='')
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "六合彩玩法表"


@reversion.register()
class Odds(models.Model):
    result = models.CharField(verbose_name="结果", max_length=25)
    result_en = models.CharField(verbose_name="结果(en)", max_length=25, default='')
    play = models.ForeignKey(Play, on_delete=models.DO_NOTHING)
    odds = models.DecimalField(verbose_name="赔率", max_digits=10, decimal_places=2,
                               default=0.00)
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "六合彩结果赔率表"


@reversion.register()
class OpenPrice(models.Model):
    issue = models.CharField(verbose_name="期号", max_length=3)
    flat_code = models.CharField(verbose_name="平码", max_length=100, default='')
    special_code = models.CharField(verbose_name="特码", max_length=2, default='')
    animal = models.CharField(verbose_name="生肖", choices=Number.ANIMAL_CHOICE, max_length=2, default='')
    wave = models.CharField(verbose_name="波色", choices=Number.WAVE_CHOICE, max_length=1, default='')
    element = models.CharField(verbose_name="五行", choices=Number.ELEMENT_CHOICE, max_length=1, default='')
    closing = models.DateTimeField(verbose_name="封盘时间", default='')
    open = models.DateTimeField(verbose_name="开奖时间", default='')
    next_open = models.DateTimeField(verbose_name="下期开奖时间", default='')

    class Meta:
        ordering = ['-issue']
        verbose_name = verbose_name_plural = "开奖表"


@reversion.register()
class SixRecord(models.Model):
    AWAIT = 0
    CORRECT = 1
    MISTAKE = 2
    ABNORMAL = 3
    TYPE_CHOICE = (
        (AWAIT, "未开奖"),
        (CORRECT, "答对"),
        (MISTAKE, "答错"),
        (ABNORMAL, "异常"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    odds = models.ForeignKey(Odds, on_delete=models.CASCADE)
    bet = models.IntegerField(verbose_name="下注数目", default=0)
    bet_coin = models.DecimalField(verbose_name="下注金额", max_digits=15, decimal_places=3, default=0.000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=18, decimal_places=8, default=0.00000000)
    status = models.CharField(verbose_name="状态", choices=TYPE_CHOICE, max_length=1, default=AWAIT)
    created_at = models.DateTimeField(verbose_name="下注时间", auto_now_add=True)
    issue = models.CharField(verbose_name="期数", max_length=3)
    is_distribution = models.BooleanField(verbose_name="是否分配过奖金", default=False)
    num = models.CharField(verbose_name="下注号码", max_length=1000)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户下注表"
