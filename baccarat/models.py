from django.db import models
import reversion
from users.models import User
from chat.models import Club
from dragon_tiger.models import Options, Table


@reversion.register()
class Boots(models.Model):
    tid = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='b_boots_tid')
    boot_id = models.IntegerField(verbose_name="第三方靴ID", default=0)
    boot_num = models.IntegerField(verbose_name="靴号", default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "靴号表"


@reversion.register()
class Number_tab(models.Model):
    NULL = 0
    BANKER = 1
    PLAYER = 2
    TIE = 3

    OPENING_LIST = (
        (NULL, "空"),
        (BANKER, "庄"),
        (PLAYER, "闲"),
        (TIE, "和")
    )
    NULL = 0
    PLAYERPAIR = 1
    BANKERPAIR = 2
    BOTHPAIR = 3

    PAIR_LIST = (
        (NULL, "空"),
        (PLAYERPAIR, "庄对"),
        (BANKERPAIR, "闲对"),
        (BOTHPAIR, "庄/闲 对")
    )
    NULL = 0
    PLAYERPAIR = 1
    BANKERPAIR = 2
    BOTHPAIR = 3

    BET_LIST = (
        (NULL, "尚未接受下注"),
        (PLAYERPAIR, "接受下注"),
        (BANKERPAIR, "停止下注-等待开盘"),
        (BOTHPAIR, "已开奖")
    )
    tid = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='b_number_tab_tid')
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='b_number_tab_boots_id')
    number_tab_id = models.IntegerField(verbose_name="第三方局ID", default=0)
    number_tab_number = models.IntegerField(verbose_name="局号", default=0)
    opening = models.CharField(verbose_name="开局结果", choices=OPENING_LIST, max_length=1, default=NULL)
    pair = models.CharField(verbose_name="开局结果（对子）", choices=PAIR_LIST, max_length=1, default=NULL)
    previous_number_tab_id = models.IntegerField(verbose_name="第三方上一局ID号", default=0)
    bet_statu = models.CharField(verbose_name="本局状态", choices=BET_LIST, max_length=1, default=NULL)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "局数表"


@reversion.register()
class Showroad_baccarat(models.Model):
    BANKER = 1
    PLAYER = 2
    TIE = 3

    OPENING_LIST = (
        (BANKER, "庄"),
        (PLAYER, "闲"),
        (TIE, "和")
    )

    NULL = 0
    PLAYERPAIR = 1
    BANKERPAIR = 2
    BOTHPAIR = 3

    PAIR_LIST = (
        (NULL, "空"),
        (PLAYERPAIR, "庄对"),
        (BANKERPAIR, "闲对"),
        (BOTHPAIR, "庄/闲 对")
    )

    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='_b_showroad_boots')
    result_show = models.CharField(verbose_name="结果", choices=OPENING_LIST, max_length=1, default=BANKER)
    order_show = models.IntegerField(verbose_name="排序", default=1)
    show_x_show = models.IntegerField(verbose_name="铺的横坐标", default=1)
    show_y_show = models.IntegerField(verbose_name="铺的竖坐标", default=1)
    pair = models.CharField(verbose_name="开局结果（对子）", choices=PAIR_LIST, max_length=1, default=NULL)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "结果路图"


@reversion.register()
class Bigroad_baccarat(models.Model):
    BANKER = 1
    PLAYER = 2
    TIE = 3

    OPENING_LIST = (
        (BANKER, "庄"),
        (PLAYER, "闲"),
        (TIE, "和")
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='b_bigroad_boots')
    result_big = models.CharField(verbose_name="结果", choices=OPENING_LIST, max_length=1, default=BANKER)
    order_big = models.IntegerField(verbose_name="排序", default=1)
    show_x_big = models.IntegerField(verbose_name="铺的横坐标", default=1)
    show_y_big = models.IntegerField(verbose_name="铺的竖坐标", default=1)
    tie_num = models.IntegerField(verbose_name="是否有和", default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "大路"


@reversion.register()
class Bigeyeroad_baccarat(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "红"),
        (PLAYER, "蓝"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='b_bigeyeroad_boots')
    result_big_eye = models.CharField(verbose_name="结果", choices=OPENING_LIST, max_length=1, default=BANKER)
    order_big_eye = models.IntegerField(verbose_name="排序", default=1)
    show_x_big_eye = models.IntegerField(verbose_name="铺的横坐标", default=1)
    show_y_big_eye = models.IntegerField(verbose_name="铺的竖坐标", default=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "大眼路"


@reversion.register()
class Psthway_baccarat(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "红"),
        (PLAYER, "蓝"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='b_psthway_boots')
    result_psthway = models.CharField(verbose_name="结果", choices=OPENING_LIST, max_length=1, default=BANKER)
    order_psthway = models.IntegerField(verbose_name="排序", default=1)
    show_x_psthway = models.IntegerField(verbose_name="铺的横坐标", default=1)
    show_y_psthway = models.IntegerField(verbose_name="铺的竖坐标", default=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "小路"


@reversion.register()
class Roach_baccarat(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "红"),
        (PLAYER, "蓝"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE, related_name='b_roach_boots')
    result_roach = models.CharField(verbose_name="结果", choices=OPENING_LIST, max_length=1, default=BANKER)
    order_roach = models.IntegerField(verbose_name="排序", default=1)
    show_x_roach = models.IntegerField(verbose_name="铺的横坐标", default=1)
    show_y_roach = models.IntegerField(verbose_name="铺的竖坐标", default=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "珠盘路"


@reversion.register()
class Baccaratrecord(models.Model):
    IOS = 1
    ANDROID = 2
    HTML5 = 3
    ROBOT = 4
    SOURCE = (
        (IOS, "iOS"),
        (ANDROID, "Android"),
        (HTML5, "HTML5"),
        (ROBOT, "机器人"),
    )

    AWAIT = 0
    OPEN = 1
    ERROR = 2
    TYPE_CHOICE = (
        (AWAIT, "未开奖"),
        (OPEN, "开奖"),
        (ERROR, "异常")
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='baccaratrecord_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='baccaratrecord_club')
    number_tab = models.ForeignKey(Number_tab, on_delete=models.CASCADE, related_name='baccaratrecord_number_tab')
    option = models.ForeignKey(Options, on_delete=models.CASCADE, related_name='baccaratrecord_option')
    bets = models.DecimalField(verbose_name="下注金额", max_digits=15, decimal_places=3, default=0.000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=18, decimal_places=8, default=0.00000000)
    source = models.CharField(verbose_name="下注来源", choices=SOURCE, max_length=1, default=ROBOT)
    status = models.CharField(verbose_name="下注状态", choices=TYPE_CHOICE, max_length=1, default=AWAIT)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now_add=True)
    open_prize_time = models.DateTimeField(verbose_name="开奖时间", auto_now=True)
    is_distribution = models.BooleanField(verbose_name="是否分配过奖金", default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "百家乐记录表"