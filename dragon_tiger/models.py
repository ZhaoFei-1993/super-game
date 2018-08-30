from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin
import reversion
import time
import hashlib
from sms.models import Sms
from users.models import User
from chat.models import Club
from captcha.models import CaptchaStore
from utils.models import CodeModel


class TableManager(models.Manager):
    """
    竞猜记录数据操作
    """

    def get_token(self, three_table_id):
        appid = '58000000'  # 获取token需要参数Appid
        appsecret = '92e56d8195a9dd45a9b90aacf82886b1'  # 获取token需要参数Secret
        times = int(time.time())  # 获取token需要参数time

        array = {'appid': '58000000', 'menu': 'bet', 'tid': three_table_id}  # 龙虎斗

        m = hashlib.md5()  # 创建md5对象
        hash_str = str(times) + appid + appsecret
        hash_str = hash_str.encode('utf-8')
        m.update(hash_str)
        token = m.hexdigest()
        array['token'] = token
        list = ""
        for key in array:
            value = array[key]
            list += str(key) + str(value)
        list += appsecret
        list = list.encode('utf-8')
        sign = hashlib.sha1(list)
        sign = sign.hexdigest()
        sign = sign.upper()
        array['sign'] = sign
        in_token = {
            "connect": "api",
            "mode": "onlineLogin",
            "json": array
        }  # ws参数组装
        return in_token


@reversion.register()
class Table(models.Model):
    OPERATION = 1
    STOP = 0
    Table_STATUS = (
        (OPERATION, "正常"),
        (STOP, "停台中")
    )

    OPERATION = 0
    SHUFFLE = 1
    STOP = 2
    TABLE_IN_CHECKOU = (
        (OPERATION, "正常"),
        (SHUFFLE, "洗牌中"),
        (STOP, "停台中")
    )

    BACCARAT = 1
    DRAGON_TIGER = 2
    NAME_LIST = (
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )

    ORDINARY_ONE = 0
    ORDINARY_TWO = 1
    FREE = 2
    MODE_LIST = (
        (ORDINARY_ONE, "龙虎普通台"),
        (ORDINARY_TWO, "百家乐普通台"),
        (FREE, "百家乐免佣台")
    )

    three_table_id = models.IntegerField(verbose_name="第三方桌子ID号", default=0)
    table_name = models.CharField(verbose_name="桌子昵称", max_length=30, default='')
    game_id = models.IntegerField(verbose_name="所属游戏ID号", default=0)
    game_name = models.CharField(verbose_name="游戏昵称", choices=NAME_LIST, max_length=1, default=DRAGON_TIGER)
    mode = models.CharField(verbose_name="桌子类型", choices=MODE_LIST, max_length=1, default=ORDINARY_TWO)
    special_num = models.IntegerField(verbose_name="特殊数字，免佣台有效", default=0)
    percent_num = models.IntegerField(verbose_name="免佣百分比", default=0)
    status = models.CharField(verbose_name="桌子状态", choices=Table_STATUS, max_length=1, default=STOP)
    in_checkout = models.CharField(verbose_name="桌子状态", choices=TABLE_IN_CHECKOU, max_length=1, default=STOP)
    websocket_url = models.CharField(verbose_name="websocket的链接地址", max_length=30, default='')
    wait_time = models.IntegerField(verbose_name="等待时间", default=30)
    remake = models.CharField(verbose_name="备注", max_length=100, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)

    objects = TableManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "桌号表"


@reversion.register()
class Boots(models.Model):
    tid = models.ForeignKey(Table, on_delete=models.CASCADE)
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
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
        (TIE, "和")
    )
    NULL = 0
    PLAYERPAIR = 1
    BANKERPAIR = 2
    BOTHPAIR = 3

    PAIR_LIST = (
        (NULL, "空"),
        (PLAYERPAIR, "龙/庄 对"),
        (BANKERPAIR, "虎/闲 对"),
        (BOTHPAIR, "和 对")
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
    tid = models.ForeignKey(Table, on_delete=models.CASCADE)
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Showroad(models.Model):
    BANKER = 1
    PLAYER = 2
    TIE = 3

    OPENING_LIST = (
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
        (TIE, "和")
    )

    NULL = 0
    PLAYERPAIR = 1
    BANKERPAIR = 2
    BOTHPAIR = 3

    PAIR_LIST = (
        (NULL, "空"),
        (PLAYERPAIR, "龙/庄 对"),
        (BANKERPAIR, "虎/闲 对"),
        (BOTHPAIR, "和 对")
    )

    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Bigroad(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Bigeyeroad(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Psthway(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Roach(models.Model):
    BANKER = 1
    PLAYER = 2

    OPENING_LIST = (
        (BANKER, "龙/庄"),
        (PLAYER, "虎/闲"),
    )
    boots = models.ForeignKey(Boots, on_delete=models.CASCADE)
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
class Options(models.Model):
    BACCARAT = 1
    DRAGON_TIGER = 2
    NAME_LIST = (
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )
    types = models.CharField(verbose_name="游戏类型", choices=NAME_LIST, max_length=1, default=DRAGON_TIGER)
    title = models.CharField(verbose_name='选项标题', max_length=255)
    title_en = models.CharField(verbose_name='选项标题(英文)', max_length=255)
    odds = models.DecimalField(verbose_name='赔率', max_digits=10, decimal_places=2, default=0.00)
    sub_title = models.CharField(verbose_name='选项子标题', max_length=255, default='')
    sub_title_en = models.CharField(verbose_name='选项子标题(英文)', max_length=255, default='')
    order = models.IntegerField(verbose_name="排序", default=0)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "选项表"


@reversion.register()
class Dragontigerrecord(models.Model):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deagon_tiger_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='deagon_tiger_record_club')
    number_tab = models.ForeignKey(Number_tab, on_delete=models.CASCADE, related_name='deagon_tiger_record_number_tab')
    option = models.ForeignKey(Options, on_delete=models.CASCADE, related_name='deagon_tiger_option')
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
        verbose_name = verbose_name_plural = "投注记录表"


@reversion.register()
class BetLimit(models.Model):
    BACCARAT = 1
    DRAGON_TIGER = 2
    NAME_LIST = (
        (BACCARAT, "百家乐"),
        (DRAGON_TIGER, "龙虎斗")
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='deagon_tiger_betlimit_club')
    types = models.CharField(verbose_name="类型", choices=NAME_LIST, max_length=1, default=DRAGON_TIGER)
    bets_one = models.CharField(verbose_name='下注值1', max_length=255, default=0.01)
    bets_two = models.CharField(verbose_name='下注值2', max_length=255, default=0.02)
    bets_three = models.CharField(verbose_name='下注值3', max_length=255, default=0.03)
    bets_four = models.CharField(verbose_name='下注值4', max_length=255, default=0.04)
    red_limit = models.DecimalField(verbose_name='限红', max_digits=10, decimal_places=3, null=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "下注值控制表"


@reversion.register()
class Board(models.Model):
    SPADE = 1
    HEART = 2
    DIAMOND = 3
    CLUB = 4
    COLOR_LIST = (
        (SPADE, "黑桃"),
        (HEART, "红桃"),
        (DIAMOND, "方块"),
        (CLUB, "梅花"),
    )
    points = models.IntegerField(verbose_name="点数", default=0)
    color = models.CharField(verbose_name="类型", choices=COLOR_LIST, max_length=1, default=SPADE)
    uel = models.CharField(verbose_name='图片链接地址', max_length=255, default="")
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "扑克牌图片库"
