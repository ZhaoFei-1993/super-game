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


class UserPresentationManager(BaseManager):
    """
    推广人下级日流水表操作
    """

    def club_flow_statistics(self, user_id, club_id, bet, income):
        """

        :param user_id:            用户ID
        :param club_id:            俱乐部ID
        :param bet:               下注流水
        :param type:              类型： 1.球赛  2. 猜股票  3.六合彩  4. 龙虎斗  5.百家乐
        """
        my_inviter  = UserInvitation.objects.filter(~Q(inviter_type=2), invitee_one=user_id).first()
        if len(my_inviter) > 0:
            created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')       # 当天日期
            created_at = str(created_at_day) + ' 00:00:00'  # 创建时间

            year = datetime.date.today().year                                               # 获取当前年份
            month = datetime.date.today().month                                              # 获取当前月份
            weekDay, monthCountDay = calendar.monthrange(year, month)  # 获取当月第一天的星期和当月的总天数
            firstDay = datetime.date(year, month, day=1)             # 获取当月第一天
            lastDay = datetime.date(year, month, day=monthCountDay)       # 获取当前月份最后一天

            gradient_income_key = "GRADIENT_INCOME_" + str(club_id)      # 盈利分红梯度
            value = get_cache(gradient_income_key)
            if value is None:
                all_gradient = Gradient.objects.filter(club_id=club_id)
                value = {}
                for gradient in all_gradient:
                    if int(gradient.sources) == 1:
                        value[0] = {
                            "sources": 0,
                            "claim": 0,
                            "claim_max": gradient.claim,
                            "income_dividend": 0
                        }
                    value[gradient.sources] = {
                        "sources": gradient.sources,
                        "claim": gradient.claim,
                        "claim_max": gradient.claim_max,
                        "income_dividend": gradient.income_dividend
                    }
                set_cache(gradient_income_key, value)

            all_income = self.filter(Q(created_at__gte=firstDay) | Q(created_at__lte=lastDay), club_id=club_id, user_id=user_id).aggregate(Sum('income'))
            sum_income = all_income['income__sum'] if all_income['income__sum'] is not None else 0
            sum_income = Decimal(sum_income)+Decimal(income)

            income_dividend = 0
            for i in value:
                claim = Decimal(i["claim"])
                claim_max = Decimal(i["claim_max"])
                if sum_income >= claim and sum_income < claim_max:
                    income_dividend = Decimal(i["income_dividend"])

            data_number = self.filter(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at).count()
            if data_number > 0:
                day_data = self.get(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at)
                day_data.user_id = my_inviter.inviter.id
                day_data.club_id = club_id
                day_data.bet_water += Decimal(bet)
                day_data.dividend_water += Decimal(bet)*0.005
                day_data.income += Decimal(income)
                day_data.income_dividend += Decimal(income)*income_dividend
                day_data.save()
            else:
                day_data = UserPresentation()
                day_data.user_id = my_inviter.inviter.id
                day_data.club_id = club_id
                day_data.bet_water = Decimal(bet)
                day_data.dividend_water = Decimal(bet) * 0.005
                day_data.income = Decimal(income)
                day_data.income_dividend = Decimal(income) * income_dividend
                day_data.created_at = created_at
                day_data.save()
            inviter_coin = UserCoin.objects.get(coin_id=day_data.club.coin.id, user_id=my_inviter.inviter.id)
            inviter_coin.balance += Decimal(bet) * 0.005
            inviter_coin.save()

@reversion.register()
class UserPresentation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promotion_user')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='promotion_club')
    bet_water = models.DecimalField(verbose_name='下注流水', max_digits=32, decimal_places=10, default=0.0000000000)
    dividend_water = models.DecimalField(verbose_name='分红流水', max_digits=32, decimal_places=10, default=0.0000000000)
    income = models.DecimalField(verbose_name='盈亏', max_digits=32, decimal_places=10, default=0.0000000000)
    income_dividend = models.DecimalField(verbose_name='盈亏分红', max_digits=32, decimal_places=10, default=0.0000000000)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    objects = UserPresentationManager()
    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "推广人下级日流水表"


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