# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser)
from wc_auth.models import Admin
from django.db.models import Q, Sum
import reversion
from sms.models import Sms
from captcha.models import CaptchaStore
from utils.models import CodeModel
from users.models import User
from chat.models import Club
from base.models import BaseManager
import datetime
import calendar
from decimal import Decimal
from utils.cache import get_cache, set_cache
from users.models import UserInvitation, UserCoin
# from utils.functions import normalize_fraction
from django.db import connection
from quiz.models import Record as Quiz_Record
from marksix.models import SixRecord
from guess.models import Record as Guess_Record, RecordStockPk as Pk_Record


class UserPresentationManager(BaseManager):
    """
    推广人下级日流水表操作
    """

    def club_flow_statistics(self, real_records, source):
        """
        :param real_records:      投注记录
        :param source:            类型： 1.足球 2.篮球 3.六合彩 4.猜股票 5.股票PK 6.百家乐 7.龙虎斗
        """

        for record in real_records:
            # 用户ID
            user_id = record.user_id

            # 俱乐部ID
            if source == 1 or source == 2:
                club_id = record.roomquiz_id
            else:
                club_id = record.club_id

            # 下注流水
            if source == 1 or source == 2:
                bet = record.bet
            elif source == 3:
                bet = record.bet_coin
            else:
                bet = record.bets

            # 盈亏
            if record.earn_coin > 0:
                income = record.earn_coin - bet
            else:
                income = record.earn_coin
            # 转化为str避免失精
            bet = str(bet)
            income = str(income)

            my_inviter = UserInvitation.objects.filter(~Q(inviter_type=2), invitee_one=user_id).first()
            if my_inviter is not None:
                created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
                created_at = str(created_at_day) + ' 00:00:00'  # 创建时间
                data_number = self.filter(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at).count()
                if data_number > 0:
                    day_data = self.get(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at)
                    day_data.user_id = my_inviter.inviter.id
                    day_data.club_id = club_id
                    day_data.bet_water += Decimal(bet)
                    day_data.dividend_water += Decimal(bet) * Decimal('0.005')
                    day_data.income += Decimal(income)
                    day_data.created_at = record.created_at
                    day_data.save()
                else:
                    day_data = UserPresentation()
                    day_data.user_id = my_inviter.inviter.id
                    day_data.club_id = club_id
                    day_data.bet_water = Decimal(bet)
                    day_data.dividend_water = Decimal(bet) * Decimal('0.005')
                    day_data.income = Decimal(income)
                    day_data.created_at = record.created_at
                    day_data.save()
                inviter_coin = UserCoin.objects.get(coin_id=day_data.club.coin.id, user_id=my_inviter.inviter.id)
                inviter_coin.balance += Decimal(bet) * Decimal('0.005')
                inviter_coin.save()


@reversion.register()
class UserPresentation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promotion_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='promotion_club')
    bet_water = models.DecimalField(verbose_name='下注流水', max_digits=32, decimal_places=10, default=0.0000000000)
    dividend_water = models.DecimalField(verbose_name='分红流水', max_digits=32, decimal_places=10, default=0.0000000000)
    income = models.DecimalField(verbose_name='盈亏', max_digits=32, decimal_places=10, default=0.0000000000)
    created_at = models.DateTimeField(verbose_name="创建时间", null=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    objects = UserPresentationManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "推广人下级日流水表"


@reversion.register()
class PresentationMonth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promotion_month_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='promotion_month_club')
    income = models.DecimalField(verbose_name='盈亏', max_digits=32, decimal_places=10, default=0.0000000000)
    income_dividend = models.DecimalField(verbose_name='盈亏分红', max_digits=32, decimal_places=10, default=0.0000000000)
    proportion = models.DecimalField(verbose_name='分成比例', max_digits=5, decimal_places=2, default=0.00)
    is_receive = models.BooleanField(verbose_name="是否已经获得盈亏分红", default=False)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    # updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "推广人下级月盈利表表"


@reversion.register()
class Gradient(models.Model):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVES = 5
    SIX = 6

    TYPE_CHOICE = (
        (ONE, "1级"),
        (TWO, "2级"),
        (THREE, "3级"),
        (FOUR, "4级"),
        (FIVES, "5级"),
        (SIX, "6级"),
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='gradient_club')
    claim = models.DecimalField(verbose_name='要求下限', max_digits=32, decimal_places=8, default=0.00000000)
    claim_max = models.DecimalField(verbose_name='要求上限', max_digits=32, decimal_places=8, default=0.00000000)
    income_dividend = models.DecimalField(verbose_name='分成比例', max_digits=3, decimal_places=2, default=0.00)
    sources = models.CharField(verbose_name="资金流动类型", choices=TYPE_CHOICE, max_length=2, default=ONE)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "梯度表"


class PromotionRecordManager(BaseManager):
    """
    推广人下注记录数据库操作
    """

    def insert_record(self, user, club, record_id, bets, source, created_at):
        """
        :param user: 用户对象
        :param club: 俱乐部对象
        :param record_id: 记录表ID
        :param bets: 下注值
        :param source: 类型(1.足球 2.篮球 3.六合彩 4.猜股票 5.股票PK 6.百家乐 7.龙虎斗)
        :param created_at:创建时间
        :return:
        """
        if int(club.id) == 1:
            pass
        else:
            promotionrecord = PromotionRecord()
            promotionrecord.user = user
            promotionrecord.club = club
            promotionrecord.record_id = record_id
            promotionrecord.bets = bets
            promotionrecord.earn_coin = 0
            promotionrecord.source = source
            promotionrecord.status = 0
            promotionrecord.created_at = created_at
            promotionrecord.save()

    def insert_all(self, real_records, source, status):
        """
        批量更新推广下注记录表
        :param real_records: 投注记录
        :param source: 类型 (1.足球 2.篮球 3.六合彩 4.猜股票 5.股票PK 6.百家乐 7.龙虎斗),
        :param status:  状态 (0,未开奖 1.已开奖 2.异常)
        :return:
        """
        promotion_list = []
        # 开始处理
        if len(real_records) > 0:
            for record in real_records:
                promotion_list.append(
                    {'record_id': record.id, 'source': source, 'earn_coin': record.earn_coin, 'status': status})

            print('处理推广功能')
            arr_values = []
            for value in promotion_list:
                values_list = [str(i) for i in list(value.values())]
                arr_values.append('(\'' + '\',\''.join(values_list) + '\')')
            sql = "INSERT INTO promotion_promotionrecord (record_id, source, earn_coin, status) VALUES " + ','.join(
                arr_values)
            sql += " ON DUPLICATE KEY UPDATE earn_coin = VALUES (earn_coin), status = VALUES (status)"

            print(sql)
            with connection.cursor() as cursor:
                if sql is not False:
                    cursor.execute(sql)
        else:
            print('无需处理推广功能')


@reversion.register()
class PromotionRecord(models.Model):
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

    AWAIT = 0
    OPEN = 1
    ERROR = 2
    TYPE_CHOICE = (
        (AWAIT, "未开奖"),
        (OPEN, "开奖"),
        (ERROR, "异常")
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    record_id = models.IntegerField(verbose_name="记录表ID", default=0)
    bets = models.DecimalField(verbose_name="下注金额", max_digits=20, decimal_places=8, default=0.00000000)
    earn_coin = models.DecimalField(verbose_name="获取金额", max_digits=20, decimal_places=8, default=0.00000000)
    source = models.IntegerField(verbose_name="类型", choices=SOURCE, default=FOOTBALL)
    status = models.IntegerField(verbose_name="下注状态", choices=TYPE_CHOICE, default=AWAIT)
    created_at = models.DateTimeField(verbose_name='创建时间', null=True)

    objects = PromotionRecordManager()

    class Meta:
        ordering = ['-id']
        unique_together = ("source", "record_id")
        verbose_name = verbose_name_plural = "推广下注记录表"
