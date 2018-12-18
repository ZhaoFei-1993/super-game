# -*- coding: UTF-8 -*-
from django.db import models
from django.db.models import Max, Sum
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin
import reversion
from sms.models import Sms
from datetime import datetime, date
import time
from decimal import Decimal
import django.utils.timezone as timezone
from captcha.models import CaptchaStore
from django.conf import settings
from base.error_code import get_code
from utils.models import CodeModel
from base.models import BaseManager
from utils.functions import to_decimal
from utils.cache import get_cache, set_cache, delete_cache, incr_cache
from django.core.management import call_command
from django.db import connection


class UserManager(BaseUserManager):
    """
    用户操作
    """

    @staticmethod
    def captcha_valid(request):
        """
        验证码校验
        :return:
        """
        code = get_code(request)

        source = request.META.get('HTTP_X_API_KEY')
        if source in ['HTML5'] and settings.IS_USER_CAPTCHA_ENABLE:
            # if 'key' not in request.data or 'challenge' not in request.data:
            #     return code.API_20405_CAPTCHA_ERROR
            # key = request.data.get('key')
            # challenge = request.data.get("challenge")
            # challenge = challenge.lower()
            #
            # is_captcha_valid = CaptchaStore.objects.filter(response=challenge, hashkey=key, expiration__gt=datetime.now()).count()
            if 'key' not in request.data:
                return code.API_20405_CAPTCHA_ERROR
            key = request.data.get('key')

            #             is_captcha_valid = CaptchaStore.objects.filter(response=challenge, hashkey=key,
            #                                                            expiration__gt=datetime.now()).count()
            is_captcha_valid = CodeModel.objects.filter(key=key,
                                                        status=1).count()
            if is_captcha_valid == 0:
                return code.API_20405_CAPTCHA_ERROR

            # 验证完后删除数据库记录，避免重复使用
            CodeModel.objects.filter(key=key, status=1).delete()
        return 0


@reversion.register()
class User(AbstractBaseUser):
    WECHAT = 1
    IOS = 2
    ANDROID = 3
    HTML5 = 4
    ROBOT = 5

    REGISTER_QQ = 1
    REGISTER_WECHAT = 2
    REGISTER_TELEPHONE = 3
    REGISTER_UNKNOWN = 4
    REGISTER_CONSOLE = 5

    DISABLE = 0
    ENABLE = 1
    DELETE = 2

    USER_STATUS = (
        (DISABLE, "用户禁用"),
        (ENABLE, "用户启用"),
        (DELETE, "用户删除")
    )

    SOURCE_CHOICE = (
        (WECHAT, "微信用户"),
        (IOS, "iOS"),
        (ANDROID, "Android"),
        (HTML5, "HTML5"),
        (ROBOT, "机器人"),
    )
    REGISTER_TYPE = (
        (REGISTER_WECHAT, "微信登录"),
        (REGISTER_QQ, "QQ登录"),
        (REGISTER_TELEPHONE, "手机号码登录"),
        (REGISTER_UNKNOWN, "未知登录类型"),
        (REGISTER_CONSOLE, "系统注册"),
    )
    username = models.CharField(verbose_name="用户账号", max_length=32)
    nickname = models.CharField(verbose_name="用户昵称", max_length=20)
    register_type = models.CharField(verbose_name="注册类型", choices=REGISTER_TYPE, max_length=1, default=REGISTER_UNKNOWN)
    source = models.CharField(verbose_name="用户来源", choices=SOURCE_CHOICE, max_length=2, default=IOS)
    avatar = models.CharField(verbose_name="头像", max_length=255, default='')
    area_code = models.IntegerField(verbose_name="手机区号", default=86)
    telephone = models.CharField(verbose_name="手机号码", max_length=11, default='')
    pass_code = models.CharField(verbose_name="资金密保", max_length=32, default='')
    is_sound = models.BooleanField(verbose_name="是否开启音效", default=False)
    is_notify = models.BooleanField(verbose_name="是否开启推送", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="最后更新日期", auto_now=True)
    ip_address = models.CharField(verbose_name='注册ip', max_length=48, default='')
    status = models.CharField(verbose_name="用户状态", choices=USER_STATUS, max_length=1, default=ENABLE)
    is_robot = models.BooleanField(verbose_name="是否机器人", default=False)
    is_money = models.BooleanField(verbose_name="是否已领取注册奖励金额", default=False)
    invitation_code = models.CharField(verbose_name="邀请码", max_length=20, default='')
    is_block = models.BooleanField(verbose_name="是否被封", default=False)
    eos_code = models.IntegerField(verbose_name="EOS充值码", default=0)

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class CoinManager(BaseManager):
    """
    Coin操作
    """
    key = 'coin_data'

    @staticmethod
    def get_coin_name_by_id(coin_id):
        """
        获取货币名称
        :param  coin_id
        :return:
        """
        coin_name = ''
        if coin_id == Coin.BTC:
            coin_name = 'BTC'
        elif coin_id == Coin.ETH:
            coin_name = 'ETH'
        elif coin_id == Coin.USDT:
            coin_name = 'USDT'
        elif coin_id == Coin.INT:
            coin_name = 'INT'

        return coin_name

    @staticmethod
    def get_coin_id_by_name(coin_name):
        """
        获取货币ID
        :param  coin_name
        :return:
        """
        coin_id = 0
        if coin_name == 'BTC':
            coin_id = Coin.BTC
        elif coin_name == 'ETH':
            coin_id = Coin.ETH
        elif coin_name == 'INT':
            coin_id = Coin.INT
        elif coin_name == 'USDT':
            coin_id = Coin.USDT

        return coin_id

    def get_gsg_coin(self):
        """
        获取GSG币信息
        :return:
        """
        coins = self.get_all()
        gsg = {}
        for coin in coins:
            if coin.id == Coin.GSG:
                gsg = coin
                break

        return gsg

    def get_coins_map_id(self):
        """
        返回货币ID对应的货币数据
        :return:
        """
        coins = self.get_all()
        map_coin = {}
        for coin in coins:
            map_coin[coin.id] = coin

        return map_coin


@reversion.register()
class Coin(models.Model):
    INT = 1
    ETH = 2
    BTC = 3
    HAND = 4
    ETC = 5
    GSG = 6
    EOS = 8
    USDT = 9
    BCH = 10  # btc
    SOC = 11  # eth
    DB = 12  # eth
    WT = 13  # EOS-WT

    icon = models.CharField(verbose_name="货币图标", max_length=255)
    name = models.CharField(verbose_name="货币名称", max_length=255)
    raw_name = models.CharField(verbose_name="货币充值前名称", max_length=255, default="")
    exchange_rate = models.IntegerField(verbose_name="兑换比例", default=1)
    cash_control = models.DecimalField(verbose_name="提现下限", max_digits=10, decimal_places=3, default=0.000)
    betting_control = models.DecimalField(verbose_name="投注下限", max_digits=10, decimal_places=3, default=0.000)
    betting_toplimit = models.DecimalField(verbose_name="投注上限", max_digits=18, decimal_places=3, default=0.000)
    coin_order = models.IntegerField(verbose_name="币种顺序", default=0)
    coin_accuracy = models.IntegerField(verbose_name="币种精度", default=0)
    is_eth_erc20 = models.BooleanField(verbose_name="是否ETH代币", default=False)
    is_criterion = models.BooleanField(verbose_name="是否为垃圾币", default=False)
    is_disabled = models.BooleanField(verbose_name="是否禁用", default=False)
    is_reality = models.BooleanField(verbose_name="是否容许提现", default=0)
    is_recharge = models.BooleanField(verbose_name="是否容许充值", default=0)
    is_lock_valid = models.BooleanField(verbose_name="是否允许锁定分红", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    objects = CoinManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币种类表"


@reversion.register()
class CoinPrice(models.Model):
    coin_name = models.CharField(verbose_name="货币名称", max_length=255, default="")
    platform_name = models.CharField(verbose_name="平台名称", max_length=20, default="")
    price = models.DecimalField(verbose_name="平台价格", max_digits=32, decimal_places=18, default=0.000000000000000000)
    price_usd = models.DecimalField(verbose_name="平台价格", max_digits=32, decimal_places=18, default=0.000000000000000000)
    updated_at = models.DateTimeField(verbose_name="最后更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币平台价格表"


@reversion.register()
class CoinPriceZero(models.Model):
    coin_name = models.CharField(verbose_name="货币名称", max_length=255, default="")
    platform_name = models.CharField(verbose_name="平台名称", max_length=20, default="")
    price = models.DecimalField(verbose_name="平台价格", max_digits=32, decimal_places=18, default=0.000000000000000000)
    price_usd = models.DecimalField(verbose_name="平台价格", max_digits=32, decimal_places=18, default=0.000000000000000000)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now_add=True)
    updated_at_true = models.DateTimeField(verbose_name="真正更新时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币平台0点价格表"


@reversion.register()
class CoinOutServiceCharge(models.Model):
    value = models.DecimalField(verbose_name="比例", max_digits=10, decimal_places=4, default=0.0000)
    coin_out = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='coin_out',
                                 verbose_name="提现货币(coin表ID外键)")
    coin_payment = models.ForeignKey(Coin, on_delete=models.CASCADE, related_name='coin_payment',
                                     verbose_name="手续费支付货币(coin表ID外键)")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "提现手续费表"


@reversion.register()
class RewardCoin(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    value_ratio = models.IntegerField(verbose_name="兑换多少GSG", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "奖励兑换表"


@reversion.register()
class CoinValue(models.Model):
    # RESULTS = 0
    # POLITENESS_RESULTS = 1
    # SCORE = 2
    # TOTAL_GOAL = 3
    # RESULT = 4
    # POLITENESS_RESULT = 5
    # SIZE_POINTS = 6
    # VICTORY_GAP = 7
    # TYPE_CHOICE = (
    #     (RESULTS, "赛果"),
    #     (POLITENESS_RESULTS, "让分赛果"),
    #     (SCORE, "比分"),
    #     (TOTAL_GOAL, "总进球"),
    #     (RESULT, "胜负"),
    #     (POLITENESS_RESULT, "让分胜负"),
    #     (SIZE_POINTS, "大小分"),
    #     (VICTORY_GAP, "胜分差"),
    # )
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    # type = models.CharField(verbose_name="玩法", choices=TYPE_CHOICE, max_length=1, default=RESULTS)
    value_index = models.IntegerField(verbose_name='投注值序号', default=1)
    value = models.DecimalField(verbose_name="货币允许投注值", max_digits=10, decimal_places=3, default=0.000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "货币投注值表"


class UserCoinManager(models.Manager):
    """
    用户货币数据操作
    """
    pass


@reversion.register()
class UserCoin(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # balance = models.DecimalField(verbose_name="余额", max_digits=18, decimal_places=2, default=0.00)
    balance = models.DecimalField(verbose_name='余额', max_digits=32, decimal_places=18, default=0.000000000000000000)

    is_opt = models.BooleanField(verbose_name="是否选择", default=False)
    is_bet = models.BooleanField(verbose_name="是否为下注选择", default=False)
    address = models.CharField(verbose_name="充值地址", max_length=50, default='')

    objects = UserCoinManager()

    class Meta:
        unique_together = ["coin", "user"]
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户代币余额表"


@reversion.register()
class CoinDetail(models.Model):
    RECHARGE = 1
    REALISATION = 2
    BETS = 3
    GUESS_BETS = 13
    ACTIVITY = 4
    OPEB_PRIZE = 5
    REGISTER = 6
    OTHER = 7
    INVITE = 8
    RETURN = 9
    CASHBACK = 10
    LOCK = 11
    DEVIDEND = 12
    EXCHANGE = 13
    UNLOCK = 14
    DRAGON_TIGER = 15
    BACCARAT = 16
    MOBILE = 17
    BANKER = 18
    WATER = 19
    REWARD = 20
    BANKER_EARN = 21
    BANKER_DEFICIT = 22
    BANKER_LEVEL = 23
    BANKER_DEPOSIT = 24
    TRANSFER_GO = 25
    TRANSFER_IN = 26

    TYPE_CHOICE = (
        (RECHARGE, "充值"),
        (REALISATION, "提现"),
        (BETS, "下注"),
        (GUESS_BETS, "股票下注"),
        (DRAGON_TIGER, "龙虎斗下注"),
        (BACCARAT, "百家乐下注"),
        (ACTIVITY, "活动"),
        (OPEB_PRIZE, "开奖"),
        (REGISTER, "注册"),
        (OTHER, "系统增加"),
        (INVITE, "邀请好友"),
        (RETURN, "返还"),
        (CASHBACK, "返现"),
        (LOCK, "锁定"),
        (DEVIDEND, "分红"),
        (EXCHANGE, "兑换"),
        (UNLOCK, "解锁"),
        (MOBILE, "转账"),
        (BANKER, "确认做庄"),
        (WATER, "流水分成"),
        (REWARD, "盈亏分成"),
        (BANKER_EARN, "做庄_赚"),
        (BANKER_DEFICIT, "做庄_亏_余"),
        (BANKER_LEVEL, "做庄_平_流"),
        (BANKER_DEPOSIT, "局头押金"),
        (TRANSFER_GO, "转账_出"),
        (TRANSFER_IN, "转账_收"),

    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_name = models.CharField(verbose_name="货币名称", max_length=255, default='')
    amount = models.CharField(verbose_name="操作数额", max_length=255)
    rest = models.DecimalField(verbose_name="余额", max_digits=32, decimal_places=18, default=0.000000000000000000)
    sources = models.CharField(verbose_name="资金流动类型", choices=TYPE_CHOICE, max_length=2, default=BETS)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="操作时间", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = verbose_name_plural = "用户资金明细"


@reversion.register()
class CoinLock(models.Model):
    period = models.IntegerField(verbose_name="锁定周期", default=0)
    profit = models.DecimalField(verbose_name="收益率", max_digits=10, decimal_places=2, default=0.00)
    limit_start = models.DecimalField(verbose_name="锁定起步金额", max_digits=32, decimal_places=18,
                                      default=0.000000000000000000)
    limit_end = models.DecimalField(verbose_name="最大锁定金额", max_digits=32, decimal_places=18,
                                    default=0.000000000000000000)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "代币锁定配置"


@reversion.register()
class UserCoinLock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_lock = models.ForeignKey(CoinLock, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="锁定金额", max_digits=32, decimal_places=18,
                                 default=0.000000000000000000)
    total_amount = models.DecimalField(verbose_name="锁定总金额(不变)", max_digits=32, decimal_places=18,
                                       default=0.000000000000000000)
    end_time = models.DateTimeField(verbose_name="锁定结束时间")
    is_free = models.BooleanField(verbose_name="是否已解锁", default=False)
    is_divided = models.BooleanField(verbose_name="是否已分红", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户货币锁定记录表"


class UserCoinLockLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_coin_lock = models.ForeignKey(UserCoinLock, on_delete=models.DO_NOTHING)
    coin_lock_days = models.IntegerField(verbose_name="锁定天数", default=0)
    # amount = models.DecimalField(verbose_name="锁定金额", max_digits=10, decimal_places=10, default=0.0000000000)
    amount = models.IntegerField(verbose_name="锁定金额", default=0)
    start_time = models.DateTimeField(verbose_name="锁定开始时间")
    end_time = models.DateTimeField(verbose_name="锁定结束时间")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户货币锁定日志表"


@reversion.register()
class DailySettings(models.Model):
    days = models.IntegerField(verbose_name="签到天数", default=1)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE, default='')
    rewards = models.IntegerField(verbose_name="奖励数", default=0)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    days_delta = models.IntegerField(verbose_name="间隔天数", default=1)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "签到配置表"


class DailyLogManager(models.Manager):
    """
    每日签到数据操作
    """
    IS_SIGN_KEY = 'key_user_signed_%s_%s'

    def is_signed(self, user_id):
        """
        判断用户是否已签到
        :param user_id:
        :return:
        """
        key = self.IS_SIGN_KEY % (user_id, datetime.now().strftime('%Y-%m-%d'))
        cache_expired = 24 * 3600  # 缓存自动过期时间（秒）

        cache_sign = get_cache(key)
        if cache_sign is not None:
            return cache_sign

        user_sign = self.filter(user_id=user_id).order_by('-id').first()
        if user_sign is False:
            set_cache(key, 0, cache_expired)
            return 0

        sign_date = user_sign.sign_date.strftime("%Y%m%d%H%M%S")
        today_time = date.today().strftime("%Y%m%d%H%M%S")
        print('sign_date = ', sign_date)
        print('today_time = ', today_time)
        if int(sign_date) >= int(today_time):
            is_sign = 1
        else:
            is_sign = 0

        set_cache(key, is_sign, cache_expired)
        return is_sign

    def remove_sign_cache(self, user_id):
        """
        删除签到缓存
        :param user_id:
        :return:
        """
        key = self.IS_SIGN_KEY % (user_id, datetime.now().strftime('%Y-%m-%d'))
        delete_cache(key)


@reversion.register()
class DailyLog(models.Model):
    YESTERDAY = 1
    TODAY = 2

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.IntegerField(verbose_name="连续签到天数", default=0)
    sign_date = models.DateTimeField(verbose_name="签到时间")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    objects = DailyLogManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户签到记录表"


class MessageManager(BaseManager):
    """
    消息数据操作
    """
    key = 'message_data'


@reversion.register()
class Message(models.Model):
    GLOBAL = 1
    PUBLIC = 2
    PRIVATE = 3
    HOME = 4
    TYPE_CHOICE = (
        (GLOBAL, "系统消息"),
        (PUBLIC, "公共消息"),
        (PRIVATE, "私信"),
        (HOME, "首页公告"),
    )
    type = models.CharField(verbose_name="消息类型", choices=TYPE_CHOICE, max_length=1, default=PUBLIC)
    title = models.CharField(verbose_name="消息标题", max_length=100, default="")
    title_en = models.CharField(verbose_name="英文消息标题", max_length=100, default="")
    content = models.CharField(verbose_name="消息内容", max_length=255, default="")
    content_en = models.CharField(verbose_name="英文消息内容", max_length=255, default="")
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    objects = MessageManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "消息内容表"


class UserMessageManager(models.Manager):
    """
    用户消息数据操作
    """

    def add_system_user_message(self, user):
        """
        发送公共消息
        后台发布系统消息，当用户注册时间小于消息发布时间，则可接收到该消息
        用户在登录系统后接收到系统消息
        :param  user    用户
        :return:
        """
        # 获取所有user.created_at <= message.created_at的系统消息
        all_messages = Message.objects.get_all()
        messages = []
        message_ids = []
        for message in all_messages:
            if int(message.type) != Message.GLOBAL or message.created_at < user.created_at:
                continue
            messages.append(message)
            message_ids.append(message.id)

        if len(messages) == 0:
            return True

        # 获取用户所有已经接收到的message_id
        user_messages = self.filter(message_id__in=message_ids, user_id=user.id).values_list('message_id', flat=True)
        user_messages = list(set(user_messages))

        diff_message_ids = list(set(message_ids).difference(set(user_messages)))
        if len(diff_message_ids) == 0:
            return True

        # 差集入库
        for message in messages:
            if message.id not in diff_message_ids:
                continue
            user_message = UserMessage()
            user_message.user = user
            user_message.message = message
            if user.is_robot is False:
                user_message.save()

        return True

    def check_message_sign(self, user_id):
        """
        检测用户消息读取标识
        :param user_id:
        :return: public_sign, system_sign
        """
        user_messages = self.filter(user_id=user_id, status=0)

        messages = Message.objects.get_all()
        map_message_id = {}
        for message in messages:
            map_message_id[message.id] = message

        # 用户消息未读标识
        public_sign = 0
        for user_message in user_messages:
            message = map_message_id[user_message.message_id]
            if int(message.type) in [2, 3]:
                public_sign = 1
                break

        # 系统消息未读标识
        system_sign = 0
        for user_message in user_messages:
            message = map_message_id[user_message.message_id]
            if int(message.type) in [1]:
                system_sign = 1
                break

        return public_sign, system_sign


@reversion.register()
class UserMessage(models.Model):
    UNREAD = 0
    READ = 1
    DELETE = 2
    TYPE_CHOICE = (
        (UNREAD, "未读"),
        (READ, "已读"),
        (DELETE, "删除"),
    )
    status = models.CharField(verbose_name="消息状态", choices=TYPE_CHOICE, max_length=1, default=UNREAD)
    user = models.ForeignKey(User, verbose_name="收件人ID", on_delete=models.CASCADE)
    title = models.CharField(verbose_name="消息标题", max_length=100, default="")
    title_en = models.CharField(verbose_name="英文消息标题", max_length=100, default="")
    content = models.CharField(verbose_name="消息内容", max_length=800, default="")
    content_en = models.CharField(verbose_name="英文消息内容", max_length=800, default="")
    message = models.ForeignKey(Message, verbose_name="消息内容表外键", on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    objects = UserMessageManager()

    # def save(self, *args, **kwargs):
    #     """
    #     重写保存方法
    #     :param args:
    #     :param kwargs:
    #     :return:
    #     """
    #     title = self.title
    #     title_en = self.title_en
    #     content = self.content
    #     content_en = self.content_en
    #
    #     self.title = ''
    #     self.title_en = ''
    #     self.content = ''
    #     self.content_en = ''
    #     super().save(*args, **kwargs)
    #
    #     # 写入文件缓存
    #     user_message_id = self.id
    #     data = {
    #         'content': content,
    #         'title': title,
    #         'content_en': content_en,
    #         'title_en': title_en,
    #     }
    #     save_user_message_content(user_message_id, data)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户消息表"


class UserRechargeManager(models.Manager):
    """
    用户充值操作
    """

    @staticmethod
    def first_price(user_id):
        """
        首次充值奖励2888HAND币
        活动送Hand币,活动时间在2018年6月1日-2018年7月13日
        :return:
        """
        # 判断是否在活动时间
        start_time = time.mktime(datetime.strptime('2018-06-01 00:00:00', '%Y-%m-%d %H:%M:%S').timetuple())
        end_time = time.mktime(datetime.strptime('2018-07-14 00:00:00', '%Y-%m-%d %H:%M:%S').timetuple())
        now_time = time.mktime(datetime.now().timetuple())

        coin_reward = 2888
        if start_time <= now_time < end_time:
            # 是否首次充值，根据user recharge表有无充值记录判断
            recharge_count = UserRecharge.objects.filter(user_id=user_id).count()
            if recharge_count > 0:
                return True

            user_reward = UserCoin.objects.get(user_id=user_id, coin_id=Coin.HAND)
            user_reward.balance += to_decimal(coin_reward)
            user_reward.save()

            # 插入用户余额变更记录表
            coin_detail = CoinDetail()
            coin_detail.user_id = user_id
            coin_detail.coin_name = 'HAND'
            coin_detail.amount = '+' + str(coin_reward)
            coin_detail.rest = user_reward.balance
            coin_detail.sources = CoinDetail.ACTIVITY
            coin_detail.save()

            # 发送充值活动奖励消息
            user_message = UserMessage()
            user_message.status = UserMessage.UNREAD
            user_message.user_id = user_id
            user_message.message_id = 3
            if user_message.user.is_robot is False:
                user_message.save()

    def soc_gift_event(self, user):
        """
        soc赠送活动
        :param user:
        :return:
        """
        activity = CoinGive.objects.get(pk=2)
        end_date = activity.end_time.strftime("%Y%m%d%H%M%S")
        today_time = date.today().strftime("%Y%m%d%H%M%S")
        # 判断是否在活动时间内
        if today_time >= end_date or user.is_robot is True:
            return True

        user_id = user.id
        # 判断是否已赠送
        is_give = CoinGiveRecords.objects.filter(user_id=user_id, coin_give_id=2).count()
        if is_give > 0:
            return True
        # 判断是否达到500人数上限
        give_number = CoinGiveRecords.objects.filter(is_recharge_lock=1, coin_give_id=2).count()
        if give_number >= 500:
            return True
        # 判断是否达到赠送条件
        sum_amount_list = self.objects.filter(user_id=user_id, coin_id=11).aggregate(
            Sum('amount'))
        sum_amount = sum_amount_list['amount__sum'] if sum_amount_list['amount__sum'] is not None else 0
        if sum_amount < 100:
            return True

        user_coin = UserCoin.objects.filter(coin_id=activity.coin_id, user_id=user_id).first()
        user_coin_give_records = CoinGiveRecords()
        user_coin_give_records.start_coin = user_coin.balance
        user_coin_give_records.user = user
        user_coin_give_records.coin_give = activity
        user_coin_give_records.lock_coin = activity.number
        user_coin_give_records.save()

        user_message = UserMessage()
        user_message.status = 0
        user_message.user = user
        user_message.message_id = 11
        if user.is_robot is False:
            user_message.save()

        coin_bankruptcy = CoinDetail()
        coin_bankruptcy.user = user
        coin_bankruptcy.coin_name = 'SOC'
        coin_bankruptcy.amount = '+' + str(activity.number)
        coin_bankruptcy.rest = to_decimal(user_coin.balance)
        coin_bankruptcy.sources = 4
        if user.is_robot is False:
            coin_bankruptcy.save()


@reversion.register()
class UserRecharge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    # amount = models.DecimalField(verbose_name="充值数量", max_digits=10, decimal_places=3, default=0.000)
    address = models.CharField(verbose_name="充值地址", max_length=255, default="")
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    amount = models.DecimalField(verbose_name='充值数量', max_digits=20, decimal_places=8, default=0)
    confirmations = models.IntegerField(verbose_name='确认数', default=0)
    txid = models.CharField(verbose_name='所在区块Hash', max_length=255, default=' ')
    trade_at = models.DateTimeField(verbose_name='交易时间', default=timezone.now)
    confirm_at = models.DateTimeField(verbose_name='确认时间', auto_now=True)

    objects = UserRechargeManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户充值记录"


@reversion.register()
class UserPresentation(models.Model):
    APPLICATION = 0
    ADOPT = 1
    REFUSE = 2

    TYPE_CHOICE = (
        (APPLICATION, "提现申请中"),
        (ADOPT, "提现成功"),
        (REFUSE, "提现失败"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    amount = models.DecimalField(verbose_name="提现数量", max_digits=32, decimal_places=18, default=0.000000000000000000)
    rest = models.DecimalField(verbose_name='剩余数量', max_digits=32, decimal_places=18, default=0.000000000000000000)
    address = models.CharField(verbose_name="提现ETH地址", max_length=255, default="")
    address_name = models.CharField(verbose_name="提现地址名称", max_length=255, default="")
    status = models.CharField(verbose_name="消息类型", choices=TYPE_CHOICE, max_length=1, default=APPLICATION)
    feedback = models.CharField(verbose_name="拒绝提现理由", max_length=255, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    is_bill = models.BooleanField(verbose_name="是否已打款", default=False)
    txid = models.TextField(verbose_name='txid地址', default="")

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "用户提现记录表"


@reversion.register()
class UserSettingOthors(models.Model):
    about = models.CharField(verbose_name="关于", max_length=150, default="")  # 序号2
    helps = models.TextField(verbose_name="帮助")  # 序号3
    reg_type = models.IntegerField(verbose_name="用户注册类型", default=1)
    sv_contractus = models.TextField(verbose_name="服务条款")  # 序号4
    pv_contractus = models.TextField(verbose_name="隐私条款")  # 序号5
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户设置其他"


class UserInvitationManager(models.Manager):
    """
    用户邀请
    """

    def activity(self, user):
        """
        邀请赠送USDT活动
        :param user:
        :return:
        """
        user_invitation_number = self.filter(money__gt=0, inviter_id=user.id, inviter_type=1, status=1).count()
        if user_invitation_number > 0:
            user_invitation_info = self.filter(money__gt=0, inviter_id=user.id, inviter_type=1, status=1)
            for a in user_invitation_info:
                login_number = LoginRecord.objects.filter(user_id=a.invitee_one).count()
                if login_number > 0:
                    try:
                        userbalance = UserCoin.objects.get(coin_id=a.coin, user_id=user.id)
                    except UserCoin.DoesNotExist:
                        return 0
                    # if int(a.coin) == 9:
                    #     a.is_deleted = 1
                    #     a.save()
                    #     usdt_balance.balance += a.money
                    #     usdt_balance.save()
                    #     coin_detail = CoinDetail()
                    #     coin_detail.user = user
                    #     coin_detail.coin_name = 'USDT'
                    #     coin_detail.amount = '+' + str(a.money)
                    #     coin_detail.rest = usdt_balance.balance
                    #     coin_detail.sources = 8
                    #     coin_detail.save()
                    #     usdt_give = CoinGiveRecords.objects.get(user_id=user.id, coin_give_id=1)
                    #     usdt_give.lock_coin += a.money
                    #     usdt_give.save()
                    # else:
                    userbalance.balance += a.money
                    userbalance.save()

                    coin = Coin.objects.get_one(pk=a.coin)

                    coin_detail = CoinDetail()
                    coin_detail.user = user
                    coin_detail.coin_name = coin.name
                    coin_detail.amount = '+' + str(a.money)
                    coin_detail.rest = userbalance.balance
                    coin_detail.sources = 8
                    coin_detail.save()
                    a.status = 2
                    a.save()

                    if a.invitee_one != 0:
                        u_mes = UserMessage()  # 邀请注册成功后消息
                        u_mes.message_id = 19  # 邀请t1消息
                        u_mes.status = 0
                        u_mes.user = user

                        if user.is_robot is False:
                            u_mes.save()

    def user_activity(self, user):
        """
        邀请赠送USDT活动
        :param user:
        :return:
        """
        user_invitation_number = self.filter(money__gt=0, invitee_one=int(user.id), inviter_type=1, status=1).count()
        if user_invitation_number == 1:
            user_invitation_info = self.get(money__gt=0, invitee_one=int(user.id), inviter_type=1, status=1)
            inviter_id = int(user_invitation_info.inviter_id)
            coin_id = int(user_invitation_info.coin)
            userbalance = UserCoin.objects.get(coin_id=coin_id, user_id=inviter_id)

            userbalance.balance += user_invitation_info.money
            userbalance.save()

            coin = Coin.objects.get_one(pk=coin_id)

            coin_detail = CoinDetail()
            coin_detail.user_id = inviter_id
            coin_detail.coin_name = coin.name
            coin_detail.amount = '+' + str(user_invitation_info.money)
            coin_detail.rest = userbalance.balance
            coin_detail.sources = 8
            coin_detail.save()
            user_invitation_info.status = 2
            user_invitation_info.save()

            u_mes = UserMessage()  # 邀请注册成功后消息
            u_mes.status = 0
            u_mes.user_id = inviter_id
            u_mes.message_id = 19  # 邀请t1消息
            if user.is_robot is False:
                u_mes.save()


@reversion.register()
class UserInvitation(models.Model):
    OLD = 0
    ROBOT = 1
    PROMOTION = 2

    INVITER_TYPE = (
        (OLD, "旧数据"),
        (PROMOTION, "推广人"),
        (ROBOT, "机器人")
    )
    INVALID = 0
    UNACCALIMED = 1
    RECEIVED = 2

    INVITER_STATUS = (
        (INVALID, "无效"),
        (UNACCALIMED, "未领取"),
        (RECEIVED, "已领取")
    )
    inviter = models.ForeignKey(User, on_delete=models.CASCADE)
    invitee_one = models.IntegerField(verbose_name="T1被邀请人id", default=0)
    invitee_two = models.IntegerField(verbose_name="T2被邀请人id", default=0)
    invitation_code = models.CharField(verbose_name="邀请码", max_length=20, default='')
    money = models.IntegerField(verbose_name="奖励金额", default=0)
    coin = models.IntegerField(verbose_name="币种ID", default=4)
    inviter_type = models.CharField(verbose_name="邀请类型", choices=INVITER_TYPE, max_length=1, default=OLD)
    status = models.CharField(verbose_name="状态", choices=INVITER_STATUS, max_length=1, default=INVALID)
    created_at = models.DateTimeField(verbose_name="邀请时间", auto_now_add=True)

    objects = UserInvitationManager()

    class Meta:
        verbose_name = verbose_name_plural = "用户邀请表"


@reversion.register()
class IntegralPrize(models.Model):
    prize_name = models.CharField(verbose_name="奖品名称", max_length=150, default="")
    icon = models.CharField(verbose_name="奖品图标", max_length=255, default="")
    prize_number = models.DecimalField(verbose_name="奖品奖励数量", max_digits=32, decimal_places=18,
                                       default=0.000000000000000000)
    prize_consume = models.DecimalField(verbose_name="抽奖消耗", max_digits=10, decimal_places=3, default=0.000)
    prize_weight = models.IntegerField(verbose_name="奖品权重", default=0)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    is_fictitious = models.BooleanField(verbose_name="是否虚拟", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "积分奖品表"


@reversion.register()
class IntegralPrizeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prize = models.ForeignKey(IntegralPrize, on_delete=models.CASCADE)
    is_receive = models.BooleanField(verbose_name="是否已领取奖励", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "积分奖品记录表"


class LoginRecordManager(models.Manager):
    """
    登录记录数据操作
    """
    key_daily_login = 'key_user_login_'

    def log(self, request, is_login=False):
        """
        登录记录
        :param request:     请求数据
        :param is_login:    是否在登录接口请求
        :return:
        """
        key = self.key_daily_login + datetime.now().strftime('%Y%m%d')
        daily_login = get_cache(key)
        # user info接口调用的一天只记录一次
        if daily_login is not None and is_login is False:
            return True

        login_record = LoginRecord()
        login_record.user_id = request.user.id
        login_record.login_type = request.META.get('HTTP_X_API_KEY', '')
        login_record.ip = request.META.get('REMOTE_ADDR', '')
        login_record.save()

        set_cache(key, '1', 24 * 3600)


@reversion.register()
class LoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_type = models.CharField(verbose_name='登录手机类型', max_length=48, default='')
    ip = models.CharField(verbose_name='登录ip', max_length=48)
    login_time = models.DateTimeField(verbose_name='登录时间', auto_now=True)

    objects = LoginRecordManager()


@reversion.register()
class BankruptcyRecords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_name = models.CharField(verbose_name="货币名称", max_length=255, default='')
    money = models.DecimalField(verbose_name='金额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "破产记录表"


@reversion.register()
class CoinInstall(models.Model):
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
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    type = models.CharField(verbose_name="玩法", choices=TYPE_CHOICE, max_length=1, default=RESULTS)
    betting_control = models.DecimalField(verbose_name="投注下限", max_digits=32, decimal_places=18,
                                          default=0.000000000000000000)
    betting_toplimit = models.DecimalField(verbose_name="投注上限", max_digits=32, decimal_places=18,
                                           default=0.000000000000000000)

    class Meta:
        verbose_name = verbose_name_plural = "投注值表"


class CoinGiveManager(models.Manager):
    """
    货币赠送数据操作
    """

    def coin_activity(self, user):
        """
        USDT赠送活动
        :param: user 用户
        :return:
        """
        activity = self.get(pk=1)
        end_date = activity.end_time.strftime("%Y%m%d%H%M%S")
        today_time = date.today().strftime("%Y%m%d%H%M%S")
        # 判断是否在活动时间内
        if today_time >= end_date or user.is_robot is True:
            return True

        user_id = user.id
        # 判断是否已赠送
        is_give = CoinGiveRecords.objects.filter(user_id=user_id, coin_give=1).count()
        if is_give > 0:
            return True

        user_coin = UserCoin.objects.filter(coin_id=activity.coin_id, user_id=user_id).first()
        user_coin_give_records = CoinGiveRecords()
        user_coin_give_records.start_coin = user_coin.balance
        user_coin_give_records.user = user
        user_coin_give_records.coin_give = activity
        user_coin_give_records.lock_coin = activity.number
        user_coin_give_records.save()
        user_coin.balance += activity.number
        user_coin.save()

        user_message = UserMessage()
        user_message.status = 0
        user_message.user = user
        user_message.message_id = 11
        if user.is_robot is False:
            user_message.save()

        coin_bankruptcy = CoinDetail()
        coin_bankruptcy.user = user
        coin_bankruptcy.coin_name = 'USDT'
        coin_bankruptcy.amount = '+' + str(activity.number)
        coin_bankruptcy.rest = to_decimal(user_coin.balance)
        coin_bankruptcy.sources = 4
        if user.is_robot is False:
            coin_bankruptcy.save()


@reversion.register()
class CoinGive(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    number = models.DecimalField(verbose_name='赠送金额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    ask_number = models.DecimalField(verbose_name='要求金额', max_digits=32, decimal_places=18,
                                     default=0.000000000000000000)
    match_number = models.IntegerField(verbose_name="要求局数", default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    end_time = models.DateTimeField(verbose_name="结束日期", auto_now=True)

    objects = CoinGiveManager()

    class Meta:
        verbose_name = verbose_name_plural = "货币赠送活动表"


@reversion.register()
class CoinGiveRecords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coin_give = models.ForeignKey(CoinGive, on_delete=models.CASCADE)
    is_recharge_give = models.BooleanField(verbose_name="是否已获得赠送金额", default=False)
    is_recharge_lock = models.BooleanField(verbose_name="是否已获得锁定金额", default=False)
    start_coin = models.DecimalField(verbose_name='开始余额', max_digits=32, decimal_places=18,
                                     default=0.000000000000000000)
    lock_coin = models.DecimalField(verbose_name='锁定金额', max_digits=32, decimal_places=18,
                                    default=10.000000000000000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "货币赠送活动表"


@reversion.register()
class IntInvitation(models.Model):
    inviter = models.ForeignKey(User, on_delete=models.CASCADE)
    invitee = models.IntegerField(verbose_name="被邀请人id", default=0)
    coin = models.IntegerField(verbose_name="INT货币表ID", default=0)
    is_block = models.BooleanField(verbose_name="是否被封", default=False)
    invitation_code = models.CharField(verbose_name="邀请码", max_length=20, default='')
    money = models.DecimalField(verbose_name='锁定金额', max_digits=32, decimal_places=18, default=10.000000000000000000)
    is_deleted = models.BooleanField(verbose_name="是否有奖励", default=True)
    created_at = models.DateTimeField(verbose_name="邀请时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "INT活动邀请表"


@reversion.register()
class Countries(models.Model):
    code = models.CharField(verbose_name="代码", max_length=2, default="")
    area_code = models.IntegerField(verbose_name="手机区号", default=0)
    name_en = models.CharField(verbose_name="名称（英文)", max_length=255, default="")
    name_zh_CN = models.CharField(verbose_name="名称（简体中文）", max_length=255, default="")
    name_zh_HK = models.CharField(verbose_name="名称（繁体中文）", max_length=255, default="")
    language = models.CharField(verbose_name="语言", max_length=255, default="")
    status = models.BooleanField(verbose_name="是否显示", default=True)

    class Meta:
        verbose_name = verbose_name_plural = "电话号码区号表"


@reversion.register()
class Robot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.BooleanField(verbose_name="是否可疑", default=False)
    created_at = models.DateTimeField(verbose_name="注册日期", default='1970-01-01 00:00:00')
    log_at = models.DateTimeField(verbose_name="登录日期", default='1970-01-01 00:00:00')

    class Meta:
        verbose_name = verbose_name_plural = "可疑用户表"


class DividendConfig(models.Model):
    dividend = models.DecimalField(verbose_name="分红总额", max_digits=10, decimal_places=2, default=0.00)
    dividend_date = models.DateTimeField(verbose_name="分红日期")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户分红配置表"


class DividendConfigCoin(models.Model):
    dividend_config = models.ForeignKey(DividendConfig, on_delete=models.DO_NOTHING)
    coin = models.ForeignKey(Coin, on_delete=models.DO_NOTHING)
    scale = models.FloatField(verbose_name="比例", default=0.00)
    price = models.FloatField(verbose_name="价格（单位:USD）", default=0.00)
    amount = models.FloatField(verbose_name="盈利数量", default=0.0000000)
    dividend_price = models.FloatField(verbose_name="实际总分红", default=0.0000000)
    coin_dividend = models.FloatField(verbose_name="每GSG实际分红", default=0.0000000)
    coin_titular_dividend = models.FloatField(verbose_name="每GSG名义分红", default=0.0000000)
    revenue = models.FloatField(verbose_name="营收数值", default=0.0000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户分红货币配置表"


@reversion.register()
class Dividend(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    user_lock = models.ForeignKey(UserCoinLock, on_delete=models.CASCADE)
    divide = models.DecimalField(verbose_name="分红额", max_digits=32, decimal_places=18, default=0.000000000000000000)
    divide_config = models.ForeignKey(DividendConfig, on_delete=models.DO_NOTHING, related_name="user_dividend")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户分红表"


@reversion.register()
class GSGAssetAccount(models.Model):
    NORMAL = 0
    LOCKED = 1
    SUPER = 2

    TYPE_CHOICE = (
        (NORMAL, "普通账户"),
        (LOCKED, "锁定账号"),
        (SUPER, "总账户"),
    )
    account_name = models.CharField(verbose_name="账号名", max_length=32, default="")
    chain_address = models.CharField(verbose_name="链上账号地址", max_length=255, default="")
    account_type = models.CharField(verbose_name="账户类型", choices=TYPE_CHOICE, max_length=1, default=NORMAL)
    balance = models.DecimalField(verbose_name="余额", max_digits=32, decimal_places=18, default=0.000000000000000000)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "GSG账号表"


@reversion.register()
class FoundationAccount(models.Model):
    CORNERSTONE = 0
    ICO = 1
    PRIVATE = 2

    TYPE_CHOICE = (
        (CORNERSTONE, "基石"),
        (ICO, "ICO"),
        (PRIVATE, "私募"),
    )
    account_name = models.CharField(verbose_name="账号名", max_length=32, default="")
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    chain_address = models.CharField(verbose_name="链上账号地址", max_length=255, default="")
    type = models.CharField(verbose_name="集资类型", choices=TYPE_CHOICE, max_length=1, default=ICO)
    balance = models.DecimalField(verbose_name="金额", max_digits=32, decimal_places=18, default=0.000000000000000000)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "私募ICO基石表"


@reversion.register()
class Expenditure(models.Model):
    WAGES = 0
    WATER = 1
    ELECTRIC = 2
    OTHER = 3

    TYPE_CHOICE = (
        (WAGES, '工资'),
        (WATER, '水费'),
        (ELECTRIC, '电费'),
        (OTHER, '其他')
    )

    year = models.CharField(verbose_name="年", max_length=20, default="")
    month = models.CharField(verbose_name="月", max_length=20, default="")
    type = models.CharField(verbose_name="类型", choices=TYPE_CHOICE, max_length=1, default="")
    in_out = models.BooleanField(verbose_name="收入(1)支出(0)", default=0)
    amount = models.DecimalField(verbose_name="金额(RMB)", max_digits=32, decimal_places=2, default=0.00)
    text = models.CharField(verbose_name="说明", max_length=32, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "公司财务"


class PreReleaseUnlockMessageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    user_message = models.ForeignKey(UserMessage, on_delete=models.DO_NOTHING)
    user_coin_lock = models.ForeignKey(UserCoinLock, on_delete=models.DO_NOTHING)
    is_delete = models.BooleanField(verbose_name="是否删除状态", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "GSG锁定即将到期提醒信息日志表"


class DividendHistory(models.Model):
    date = models.CharField(verbose_name="日期", max_length=20, default="")
    locked = models.DecimalField(verbose_name="锁定数量", max_digits=32, decimal_places=2, default=0.00)
    deadline = models.DecimalField(verbose_name="当日到期数量", max_digits=32, decimal_places=2, default=0.00)
    newline = models.DecimalField(verbose_name="当日新增数量", max_digits=32, decimal_places=2, default=0.00)
    truevalue = models.DecimalField(verbose_name="实际分红额", max_digits=32, decimal_places=8, default=0)
    revenuevalue = models.DecimalField(verbose_name="营收分红额", max_digits=32, decimal_places=8, default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="创建时间", auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "GSG历史分红列表"


class EosCodeManager(models.Manager):
    """
    EOS充值码数据操作
    """
    key_daily_eos_code = 'key_daily_eos_code'
    key_daily_eos_code_index = 'key_daily_eos_code_index'

    def get_eos_code(self):
        """
        获取一个EOS CODE，从0个读取，依次递增
        :return:
        """
        if settings.IS_ENABLE_USER_EOS_CODE is False:
            return 0

        # TODO: 考虑并发情况进行处理，使用Redis锁机制
        eos_codes = get_cache(self.key_daily_eos_code)
        index = get_cache(self.key_daily_eos_code_index)
        if index is None or index == -1:
            index = 0
            set_cache(self.key_daily_eos_code_index, index)
        else:
            incr_cache(self.key_daily_eos_code_index)
        index = get_cache(self.key_daily_eos_code_index)

        eos_code = eos_codes[index]
        # 当缓存中可用的码只剩下100个的时候，重新生成缓存
        if len(eos_codes) - index <= 100:
            call_command('eos_code_recache')

        return int(eos_code[0])


class EosCode(models.Model):
    code = models.IntegerField(verbose_name="EOS充值编号")
    is_good_code = models.BooleanField(verbose_name="是否靓号", default=False)
    is_used = models.BooleanField(verbose_name="用户ID", default=False)

    objects = EosCodeManager()

    class Meta:
        verbose_name = verbose_name_plural = "EOS充值编号生成表"


class MobileCoin(models.Model):
    """
    转账记录表
    """
    sponsor = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='sponsor_user', verbose_name="委托人id")
    recipient = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='recipient_user',
                                  verbose_name="接受人id")
    coin = models.ForeignKey(Coin, on_delete=models.DO_NOTHING, related_name='mobile_coin', verbose_name="货币id")
    remarks = models.CharField(verbose_name="备注", max_length=255, default='')
    balance = models.DecimalField(verbose_name='操作金额', max_digits=32, decimal_places=18, default=0.000000000000000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "转账记录表"


class RecordMarkManager(BaseManager):
    """
    记录标记表数据库操作
    """

    def insert_record_mark(self, user_id, rule=0):
        """
        录入记录标记表(单)
        :param user_id:用户ID
        :param rule: 类型 (1.足球, 2.六合彩, 3.猜股票, 4.龙虎斗, 5.百家乐, 6.股票PK, 7.篮球, 8.公告）
        :return:
        """
        record_mark_number = RecordMark.objects.filter(user_id=int(user_id)).count()
        if int(record_mark_number) == 0:
            record_mark = RecordMark()
            record_mark.user_id = user_id
            if int(rule) == 1:
                record_mark.quiz_football = 0
                record_mark.message = 1
            elif int(rule) == 7:
                record_mark.quiz_basketball = 0
                record_mark.message = 1
            elif int(rule) == 2:
                record_mark.six = 0
                record_mark.message = 1
            elif int(rule) == 3:
                record_mark.guess = 0
                record_mark.message = 1
            elif int(rule) == 4:
                record_mark.dragon_tiger = 0
                record_mark.message = 1
            elif int(rule) == 5:
                record_mark.baccarat = 0
                record_mark.message = 1
            elif int(rule) == 6:
                record_mark.guess_pk = 0
                record_mark.message = 1
            else:
                record_mark.message = 1
            record_mark.save()
        else:
            record_mark = self.get(user_id=user_id)
        return record_mark

    def update_record_mark(self, user_id, rule, status):
        """
        更新记录标记表
        :param user_id: 用户ID
        :param rule: 类型 (1.足球, 2.六合彩, 3.猜股票, 4.龙虎斗, 5.百家乐, 6.股票PK, 7.篮球, 8.公告）
        :param status: 状态 0已读，1未读
        :return:
        """
        record_mark_number = RecordMark.objects.filter(user_id=int(user_id)).count()
        if int(record_mark_number) == 0:
            self.insert_record_mark(user_id, rule)
            record_mark = self.get(user_id=int(user_id))
            if int(rule) == 1:
                record_mark.quiz_football = int(status)
                record_mark.message = 1
            elif int(rule) == 7:
                record_mark.quiz_basketball = int(status)
                record_mark.message = 1
            elif int(rule) == 2:
                record_mark.six = int(status)
                record_mark.message = 1
            elif int(rule) == 3:
                record_mark.guess = int(status)
                record_mark.message = 1
            elif int(rule) == 4:
                record_mark.dragon_tiger = int(status)
                record_mark.message = 1
            elif int(rule) == 5:
                record_mark.baccarat = int(status)
                record_mark.message = 1
            elif int(rule) == 6:
                record_mark.guess_pk = int(status)
                record_mark.message = 1
            else:
                record_mark.message = int(status)
            record_mark.save()
        else:
            record_mark = self.get(user_id=int(user_id))
            if int(rule) == 1:
                record_mark.quiz_football = int(status)
            elif int(rule) == 7:
                record_mark.quiz_basketball = int(status)
            elif int(rule) == 2:
                record_mark.six = int(status)
            elif int(rule) == 3:
                record_mark.guess = int(status)
            elif int(rule) == 4:
                record_mark.dragon_tiger = int(status)
            elif int(rule) == 5:
                record_mark.baccara = int(status)
            elif int(rule) == 6:
                record_mark.guess_pk = int(status)
            else:
                record_mark.message = int(status)
            record_mark.save()

    def insert_all_record_mark(self, user_list, rule):
        """
        批量更新记录标记表
        :param user_list: 用户ID 例子：[1,2,3,4]
        :param rule: 类型 (1.足球, 2.六合彩, 3.猜股票, 4.龙虎斗, 5.百家乐, 6.股票PK, 7.篮球, 8.公告）
        :return:
        """
        sql = ""
        if len(user_list) > 0:
            list = [str(i) for i in user_list]
            key = ", 1), ("
            if int(rule) == 1:
                record_list = "user_id, quiz_football"
                keys = "quiz_football = VALUES (quiz_football)"
            elif int(rule) == 7:
                record_list = "user_id, quiz_basketball"
                keys = "quiz_basketball = VALUES (quiz_basketball)"
            elif int(rule) == 2:
                record_list = "user_id, six"
                keys = "six = VALUES (six)"
            elif int(rule) == 3:
                record_list = "user_id, guess"
                keys = "guess = VALUES (guess)"
            elif int(rule) == 4:
                record_list = "user_id, dragon_tiger"
                keys = "dragon_tiger = VALUES (dragon_tiger)"
            elif int(rule) == 5:
                record_list = "user_id, baccarat"
                keys = "baccarat = VALUES (baccarat)"
            else:
                record_list = "user_id, guess_pk"
                keys = "guess_pk = VALUES (guess_pk)"

            sql = "INSERT INTO users_recordmark (" + record_list + ") VALUES (" + key.join(
                list) + ", 1)"
            sql += " ON DUPLICATE KEY UPDATE " + keys
        else:
            if int(rule) == 7:
                sql = "UPDATE users_recordmark SET message = 1"
        with connection.cursor() as cursor:
            if sql is not False:
                print(sql)
                cursor.execute(sql)


@reversion.register()
class RecordMark(models.Model):
    """
    记录标记表
    """
    AWAIT = 0
    OPEN = 1
    TYPE_CHOICE = (
        (AWAIT, "已读"),
        (OPEN, "未读"),
    )
    user_id = models.IntegerField(verbose_name="用户ID", default=0)
    quiz_football = models.IntegerField(verbose_name="足球", choices=TYPE_CHOICE, default=AWAIT)
    quiz_basketball = models.IntegerField(verbose_name="篮球", choices=TYPE_CHOICE, default=AWAIT)
    guess = models.IntegerField(verbose_name="股票", choices=TYPE_CHOICE, default=AWAIT)
    guess_pk = models.IntegerField(verbose_name="股票PK", choices=TYPE_CHOICE, default=AWAIT)
    six = models.IntegerField(verbose_name="六合彩", choices=TYPE_CHOICE, default=AWAIT)
    dragon_tiger = models.IntegerField(verbose_name="龙虎斗", choices=TYPE_CHOICE, default=AWAIT)
    baccarat = models.IntegerField(verbose_name="百家乐", choices=TYPE_CHOICE, default=AWAIT)
    message = models.IntegerField(verbose_name="公告", choices=TYPE_CHOICE, default=AWAIT)

    objects = RecordMarkManager()

    class Meta:
        verbose_name = verbose_name_plural = "记录标记表"
