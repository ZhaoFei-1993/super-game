from django.db import models
from wc_auth.models import Admin
from mptt.models import MPTTModel
from users.models import Coin, User, CoinValue
from chat.models import Club
import reversion


@reversion.register()
class Stock(models.Model):
    SSE = 0
    SHENZHEN = 1
    HANGSENG = 2
    DOWJONES = 3
    NASDAQ = 4

    STOCK = (
        (SSE, "上证指数"),
        (SHENZHEN, "深证成指"),
        (HANGSENG, "恒生指数"),
        (DOWJONES, "道琼斯"),
        (NASDAQ, "纳斯达克"),
    )

    SSE = 0
    SHENZHEN = 1
    HANGSENG = 2
    DOWJONES = 3
    NASDAQ = 4

    STOCK_EN = (
        (SSE, "SSE"),
        (SHENZHEN, "SZSE"),
        (HANGSENG, "HSI"),
        (DOWJONES, "DJI"),
        (NASDAQ, "NASDAQ"),
    )
    name = models.CharField(verbose_name="证券名称", choices=STOCK, max_length=1, default=SSE)
    icon = models.CharField(verbose_name="股票图标", max_length=255, default='')
    name_en = models.CharField(verbose_name="证券名称(英语)", choices=STOCK_EN, max_length=1, default=SSE)
    order = models.IntegerField(verbose_name="排序", default=0)
    stock_guess_open = models.BooleanField(verbose_name="是否开启股指竞猜", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间(年月日)", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="修改时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股票配置表"


@reversion.register()
class Periods(models.Model):
    periods = models.IntegerField(verbose_name='期数，递增，不中断')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    start_value = models.DecimalField(verbose_name='开盘指数', max_digits=10, decimal_places=2, null=True)
    lottery_value = models.DecimalField(verbose_name='开奖指数', max_digits=10, decimal_places=2, null=True)
    lottery_time = models.DateTimeField(verbose_name='开奖时间', auto_now_add=True)
    start_time = models.DateTimeField(verbose_name='开始下注时间', auto_now_add=True)
    rotary_header_time = models.DateTimeField(verbose_name='封盘时间', auto_now_add=True)
    is_seal = models.BooleanField(verbose_name="是否封盘", default=False)
    up_and_down = models.CharField(verbose_name='涨跌正确选项', max_length=20, default='')
    up_and_down_en = models.CharField(verbose_name='涨跌正确选项', max_length=20, default='')
    size = models.CharField(verbose_name='大小正确选项', max_length=20, default='')
    size_en = models.CharField(verbose_name='大小正确选项', max_length=20, default='')
    points = models.CharField(verbose_name='点数正确选项', max_length=20, default='')
    pair = models.CharField(verbose_name='对子正确选项', max_length=20, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now_add=True)

    is_result = models.BooleanField(verbose_name='是否已开奖', default=False)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "期数，开奖后生成下一期记录"


@reversion.register()
class Play(models.Model):
    SIZE = 1
    POINTS = 2
    PAIR = 3
    UP_AND_DOWN = 0

    PLAY = (

        (UP_AND_DOWN, "涨跌"),
        (SIZE, "大小"),
        (POINTS, "点数"),
        (PAIR, "对子")
    )

    SIZE = 1
    POINTS = 2
    PAIR = 3
    UP_AND_DOWN = 0

    PLAY_EN = (
        (UP_AND_DOWN, "up_and_down"),
        (SIZE, "Size"),
        (POINTS, "Points"),
        (PAIR, "Pair")
    )

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    play_name = models.CharField(verbose_name="玩法", choices=PLAY, max_length=1, default=SIZE)
    play_name_en = models.CharField(verbose_name="玩法(英语)", choices=PLAY_EN, max_length=1, default=SIZE)
    tips = models.CharField(verbose_name='提示短语', max_length=255, default='')
    tips_en = models.CharField(verbose_name='提示短语(英语)', max_length=255, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "玩法表"


@reversion.register()
class BetLimit(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    bets_one = models.CharField(verbose_name='下注值1', max_length=255, default=0.01)
    bets_two = models.CharField(verbose_name='下注值2', max_length=255, default=0.02)
    bets_three = models.CharField(verbose_name='下注值3', max_length=255, default=0.03)
    bets_min = models.DecimalField(verbose_name='最小下注值', max_digits=10, decimal_places=3, null=True)
    bets_max = models.DecimalField(verbose_name='最大下注值', max_digits=10, decimal_places=3, null=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "下注值控制表"


@reversion.register()
class Options(models.Model):
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
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
class Index(models.Model):
    periods = models.ForeignKey(Periods, on_delete=models.CASCADE)
    index_value = models.DecimalField(verbose_name='指数值', max_digits=10, decimal_places=2)
    index_time = models.DateTimeField(verbose_name='指数时间', auto_now_add=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "指数记录表(时分)"


@reversion.register()
class Index_day(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    index_value = models.DecimalField(verbose_name='指数值', max_digits=10, decimal_places=2)
    index_time = models.DateTimeField(verbose_name='指数时间', auto_now_add=True)
    created_at = models.DateTimeField(verbose_name='创建时间(年月日)', auto_now_add=True)
    update_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "指数记录表(天)"


@reversion.register()
class Record(models.Model):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guess_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    periods = models.ForeignKey(Periods, on_delete=models.CASCADE)
    play = models.ForeignKey(Play, on_delete=models.CASCADE)
    options = models.ForeignKey(Options, on_delete=models.CASCADE)
    bets = models.DecimalField(verbose_name="下注金额", max_digits=15, decimal_places=3, default=0.000)
    odds = models.DecimalField(verbose_name="下注赔率", max_digits=15, decimal_places=3, default=0.000)
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

# ================ 股指pk ==================================


@reversion.register()
class StockPk(models.Model):
    left_stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='left_to_stock')
    right_stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='right_to_stock')
    left_stock_name = models.CharField(verbose_name="左股票名称", max_length=64, default='')
    right_stock_name = models.CharField(verbose_name="右股票名称", max_length=64, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股指pk玩法"


@reversion.register()
class Issues(models.Model):
    stock_pk = models.ForeignKey(StockPk, on_delete=models.CASCADE)
    left_periods = models.ForeignKey(Periods, on_delete=models.CASCADE, related_name='left_to_periods')
    right_periods = models.ForeignKey(Periods, on_delete=models.CASCADE, related_name='right_to_periods')
    left_stock_index = models.DecimalField(verbose_name='左边股指指数值', max_digits=10, decimal_places=2, default=0)
    right_stock_index = models.DecimalField(verbose_name='右边股指指数值', max_digits=10, decimal_places=2, default=0)
    size_pk_result = models.CharField(verbose_name="股指大小pk答案", max_length=100, default='')
    issue = models.IntegerField(verbose_name='期数,新的一天从1开始')

    closing = models.DateTimeField(verbose_name="封盘时间", null=True)
    open = models.DateTimeField(verbose_name="开奖时间", null=True)

    result_confirm = models.IntegerField(verbose_name="开奖指数确认数", default=0)  # 0是未确认，等于3为答案
    is_open = models.BooleanField(verbose_name="是否开奖", default=0)
    update_at = models.DateTimeField(verbose_name="开奖时间", auto_now=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    bet_sum = models.TextField(verbose_name="投注流水", default='')
    profit = models.TextField(verbose_name="盈亏状况", default='')

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股指pk期数"


@reversion.register()
class PlayStockPk(models.Model):
    PK_SIZE = 0
    PLAY = (
        (PK_SIZE, "尾数大小"),
    )

    PLAY_EN = (
        (PK_SIZE, "尾数大小"),
    )

    stock_pk = models.ForeignKey(StockPk, on_delete=models.CASCADE, )
    play_name = models.CharField(verbose_name="玩法", choices=PLAY, max_length=1, default=PK_SIZE)
    play_name_en = models.CharField(verbose_name="玩法(英语)", choices=PLAY_EN, max_length=1, default=PK_SIZE)
    tips = models.CharField(verbose_name='提示短语', max_length=255, default='')
    tips_en = models.CharField(verbose_name='提示短语(英语)', max_length=255, default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股指pk玩法"


@reversion.register()
class OptionStockPk(models.Model):
    stock_pk = models.ForeignKey(StockPk, on_delete=models.CASCADE)
    play = models.ForeignKey(PlayStockPk, on_delete=models.CASCADE)
    title = models.CharField(verbose_name='选项标题', max_length=255)
    title_en = models.CharField(verbose_name='选项标题(英文)', max_length=255)
    odds = models.DecimalField(verbose_name='赔率', max_digits=10, decimal_places=2, default=0.00)
    order = models.IntegerField(verbose_name="排序", default=0)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股指pk选项"


@reversion.register()
class RecordStockPk(models.Model):
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
    issue = models.ForeignKey(Issues, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    play = models.ForeignKey(PlayStockPk, on_delete=models.CASCADE, null=True)
    option = models.ForeignKey(OptionStockPk, on_delete=models.CASCADE, null=True)
    odds = models.DecimalField(verbose_name="下注赔率", max_digits=15, decimal_places=3, default=0.000)
    bets = models.DecimalField(verbose_name="下注金额", max_digits=15, decimal_places=3, default=0.000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=18, decimal_places=8, default=0.00000000)
    source = models.CharField(verbose_name="下注来源", choices=SOURCE, max_length=1, default=ROBOT)
    status = models.CharField(verbose_name="下注状态", choices=TYPE_CHOICE, max_length=1, default=AWAIT)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    open_prize_time = models.DateTimeField(verbose_name="开奖时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "股指pk投注记录表"
