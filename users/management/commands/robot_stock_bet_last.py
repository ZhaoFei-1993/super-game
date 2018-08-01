# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import time
from django.db import transaction
import random

from guess.models import Periods, Record, Stock
from users.models import User, Coin
from chat.models import Club


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

    @staticmethod
    def get_stock(stock_id):
        """
        获取股票名称
        :param stock_id
        :return:
        """
        stock_info = Stock.objects.get(pk=stock_id)

        stock_name = ''
        for stock in Stock.STOCK:
            sid, sname = stock
            if int(sid) == int(stock_info.name):
                stock_name = sname
                break

        return stock_name

    @staticmethod
    def get_wager(club_id):
        """
        计算不超过价值10USD的俱乐部代币
        :param club_id:
        :return:
        """
        club = Club.objects.get(pk=club_id)
        coin_id = int(club.coin_id)

        wager = 0
        if coin_id == Coin.USDT:
            wager = 10
        elif coin_id == Coin.BTC:
            wager = 0.002
        elif coin_id == Coin.ETH:
            wager = 0.03
        elif coin_id == Coin.HAND:
            wager = 100000
        elif coin_id == Coin.INT:
            wager = 100

        return wager

    @transaction.atomic()
    def handle(self, *args, **options):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # 获取是否截止下注的股指
        rotary_header = None
        current_period = None
        periods = Periods.objects.filter(is_seal=False, is_result=False)
        print('periods = ', periods)
        for period in periods:
            if str(period.rotary_header_time) < str(current_time):
                rotary_header = period
                current_period = period

                # 更新该期数为封盘状态
                prd = Periods.objects.get(pk=period.id)
                prd.is_seal = True
                prd.save()
                self.stdout.write(self.style.SUCCESS(self.get_stock(prd.stock_id) + '-' + str(prd.id)) + ' 封盘成功')
                break

        if rotary_header is None:
            raise CommandError('暂无封盘股指数据')

        raise CommandError('Done')

        clubs = Club.objects.filter(is_dissolve=False)
        for club in clubs:
            up_down_ids = {
                4: [49, 53],
                8: [50, 54],
                12: [51, 55],
                16: [52, 56],
            }
            for play_id in up_down_ids:
                records = Record.objects.filter(periods=current_period, options_id__in=up_down_ids[play_id], club=club)
                # 过滤掉无真实用户投注的情况
                if records is None:
                    self.stdout.write(self.style.SUCCESS('无下注记录'))
                    continue

                has_up_record = False
                has_down_record = False

                up_option_id, down_option_id = up_down_ids[play_id]

                for record in records:
                    if int(record.options_id) == up_option_id:
                        has_up_record = True
                    if int(record.options_id) == down_option_id:
                        has_down_record = True

                if has_up_record is True and has_down_record is True:
                    self.stdout.write(self.style.SUCCESS('两边均有用户下注'))
                    continue

                is_need_robot_bet = False
                option_id = 0
                # 只下注涨，未下注跌
                if has_up_record is True and has_down_record is False:
                    is_need_robot_bet = True
                    option_id = up_option_id

                # 只下注跌，未下注涨
                if has_up_record is False and has_down_record is True:
                    is_need_robot_bet = True
                    option_id = down_option_id

                # 是否需要机器人下注
                if is_need_robot_bet is True:
                    record = Record()
                    record.user = self.get_bet_user()
                    record.periods = current_period
                    record.club = club
                    record.play_id = play_id
                    record.options_id = option_id
                    record.bets = self.get_wager(club.id)
                    record.odds = 1
                    record.source = Record.ROBOT
                    record.save()

                    self.stdout.write(self.style.SUCCESS('下注成功。' + str(record)))

        self.stdout.write(self.style.SUCCESS(''))
