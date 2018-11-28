from django.db import models
from chat.models import Club
from users.models import User

# Create your models here.


class BankerShare(models.Model):
    """
    联合做庄： 份额表
    """
    FOOTBALL = 1
    BASKETBALL = 2
    SIX = 3
    GUESS = 4
    GUESSPK = 5
    BACCARAT = 6
    DRAGON_TIGER = 7
    SOURCE = (
        (FOOTBALL, "足球"),
        (BASKETBALL, "篮球"),
        (SIX, "六合彩"),
        (GUESS, "猜股票"),
        (GUESSPK, "股票PK"),
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )
    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_club', verbose_name="俱乐部ID")
    source = models.IntegerField(verbose_name="类型", choices=SOURCE, default=FOOTBALL)
    balance = models.DecimalField(verbose_name='份额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    proportion = models.DecimalField(verbose_name='占比', max_digits=4, decimal_places=3, default=0.000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "份额表"


class BankerRecord(models.Model):
    """
    联合做庄： 记录表
    """
    FOOTBALL = 1
    BASKETBALL = 2
    SIX = 3
    GUESS = 4
    GUESSPK = 5
    BACCARAT = 6
    DRAGON_TIGER = 7
    SOURCE = (
        (FOOTBALL, "足球"),
        (BASKETBALL, "篮球"),
        (SIX, "六合彩"),
        (GUESS, "猜股票"),
        (GUESSPK, "股票PK"),
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )

    READY = 1
    SUCCESS = 2
    FLOW_DISK = 3
    TYPE_CHOICE = (
        (READY, "未分配奖励"),
        (SUCCESS, "已分配奖励"),
        (FLOW_DISK, "流盘")
    )
    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_record_club', verbose_name="俱乐部ID")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='banker_record_user', verbose_name="用户ID")
    balance = models.DecimalField(verbose_name='让购份额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    proportion = models.DecimalField(verbose_name='份额占比', max_digits=12, decimal_places=10, default=0.0000000000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=18, decimal_places=8, default=0.00000000)
    source = models.IntegerField(verbose_name="玩法", choices=SOURCE, default=FOOTBALL)
    key_id = models.IntegerField(verbose_name="外键ID(玩法不同外键表不同)", default=0)
    status = models.IntegerField(verbose_name="是否分配奖励", choices=TYPE_CHOICE, default=READY)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "做庄记录表"


class BankerBigHeadRecord(models.Model):
    """
    联合做庄： 局头记录表
    """

    club = models.ForeignKey(Club, on_delete=models.DO_NOTHING, related_name='banker_big_head_record_club', verbose_name="俱乐部ID")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='banker_big_head_record_user', verbose_name="用户ID")
    proportion = models.DecimalField(verbose_name='局头份额占比', max_digits=3, decimal_places=2, default=0.35)
    is_receive = models.BooleanField(verbose_name="是否已有效", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    end_time = models.DateTimeField(verbose_name="失效时间", null=True)

    class Meta:
        verbose_name = verbose_name_plural = "做庄局头表表"




