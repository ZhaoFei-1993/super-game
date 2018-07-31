# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from django.db import transaction
import random

from guess.models import Periods, Record
from users.models import User


class Command(BaseCommand):
    """
    在截止下注时，机器人在没有投注的一方下注一个不超过价值10USD的俱乐部代币。
    """
    help = "系统用户自动下注-截止下注自动下注"

    @staticmethod
    def get_bet_user():
        """
        随机获取用户
        :return:
        """
        users = User.objects.filter(is_robot=True)
        secure_random = random.SystemRandom()
        return secure_random.choice(users)

    @transaction.atomic()
    def handle(self, *args, **options):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 获取是否截止下注的股指
        rotary_header = None
        current_period = None
        periods = Periods.objects.filter(is_seal=False, is_result=False)
        for period in periods:
            if str(period.rotary_header_time) < str(current_time):
                rotary_header = period
                current_period = period

                # 更新该期数为封盘状态
                period.is_seal = True
                period.save()
                break

        if rotary_header is None:
            raise CommandError('暂无封盘股指数据')

        # 判断是否达到“没有投注的一方”的条件
        # up_down_ids_1 = [49, 53]
        # up_down_ids_2 = [50, 54]
        # up_down_ids_3 = [51, 55]
        # up_down_ids_4 = [52, 56]
        # all_ids = up_down_ids_1 + up_down_ids_2 + up_down_ids_3 + up_down_ids_4
        # records = Record.objects.filter(periods=current_period, options_id__in=all_ids)
        # has_up_record = False
        # has_down_record = False
        #
        # # 只下注涨，未下注跌
        # if has_up_record is True and has_down_record is False:
        #     record = Record()
        #     record.user = self.get_bet_user()
        #     record.periods = current_period
        #     record.club = current_period
        #     record.play = rule
        #     record.options = option
        #     record.bets = wager
        #     record.odds = current_odds
        #     record.source = Record.ROBOT
        #     record.save()

        self.stdout.write(self.style.SUCCESS('下注成功'))
