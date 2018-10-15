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

        club_id = int(club_id)
        print("club_id==========================", club_id)
        print("user_id==========================", user_id)
        print("bet==========================", bet)
        print("income==========================", income)
        if club_id == 1 or club_id == 5:
            print("1111111111111111111111111")
            pass
        else:
            print("222222222222222222222222222")
            my_inviter = UserInvitation.objects.filter(~Q(inviter_type=2), invitee_one=user_id).first()
            if my_inviter is not None:
                created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')       # 当天日期
                created_at = str(created_at_day) + ' 00:00:00'  # 创建时间
                data_number = self.filter(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at).count()
                print("data_number=======================", data_number)
                if data_number > 0:
                    day_data = self.get(club_id=club_id, user_id=my_inviter.inviter.id, created_at=created_at)
                    print("day_data=========================", day_data)
                    day_data.user_id = my_inviter.inviter.id
                    day_data.club_id = club_id
                    day_data.bet_water += Decimal(bet)
                    day_data.dividend_water += Decimal(bet) * Decimal(0.005)
                    day_data.income += Decimal(income)
                    day_data.created_at = created_at
                    day_data.save()
                else:
                    day_data = UserPresentation()
                    day_data.user_id = my_inviter.inviter.id
                    day_data.club_id = club_id
                    day_data.bet_water = Decimal(bet)
                    day_data.dividend_water = Decimal(bet) * Decimal(0.005)
                    day_data.income = Decimal(income)
                    day_data.created_at = created_at
                    day_data.save()
                    print("33333333333333333333333333333333")
                inviter_coin = UserCoin.objects.get(coin_id=day_data.club.coin.id, user_id=my_inviter.inviter.id)
                print("inviter_coin===============================", inviter_coin.balance)
                inviter_coin.balance += Decimal(bet) * Decimal(0.005)
                print("112121331==================================", Decimal(bet) * Decimal(0.005))
                inviter_coin.save()
                print("inviter_coin.balance==============================", inviter_coin.balance)

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