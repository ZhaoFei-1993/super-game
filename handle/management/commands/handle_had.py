# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Rule, Option, Record
from users.models import CoinDetail, UserCoin, UserMessage, Coin
from chat.models import Club
import datetime
from utils.functions import get_club_info, normalize_fraction
from decimal import Decimal
from multiprocessing import Pool
import os


def process_main(records):
    i = 0
    for record in records:
        i += 1
        print('现在正在执行第', i, '条，一共', len(records), os.getpid())
        rule_all = Rule.objects.filter(quiz=record.quiz).all()
        rule_had = rule_all.filter(type=0).first()
        if rule_had is not None:
            option_had = Option.objects.filter(rule=rule_had, is_right=True).first()
            if record.option.option_id == option_had.id and record.earn_coin < 0:
                # 用户增加对应币金额
                club = Club.objects.get(pk=record.roomquiz_id)

                # 获取币信息
                coin = Coin.objects.get(pk=club.coin_id)

                earn_coin = record.bet * record.odds
                earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                record.type = Record.CORRECT
                record.earn_coin = earn_coin
                record.save()

                user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin.id)
                user_coin.coin_id = coin.id
                user_coin.user_id = record.user_id
                user_coin.balance = Decimal(user_coin.balance) + Decimal(earn_coin)
                user_coin.save()

                # 用户资金明细表
                coin_detail = CoinDetail()
                coin_detail.user_id = record.user_id
                coin_detail.coin_name = coin.name
                coin_detail.amount = Decimal(earn_coin)
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.OPEB_PRIZE
                coin_detail.save()

                u_mes = UserMessage()
                u_mes.status = 0
                u_mes.user_id = record.user_id
                u_mes.message_id = 6  # 私人信息
                u_mes.title = club.room_title + '开奖公告'
                u_mes.title_en = 'Lottery announcement from' + club.room_title_en
                u_mes.content = '由于系统原因导致' + record.quiz.host_team + ' VS ' + record.quiz.guest_team + '赛事结算出错,现已讲您的奖金' + str(
                    earn_coin) \
                                + '重新发放,请查收！'
                u_mes.content_en = '由于系统原因导致' + record.quiz.host_team + ' VS ' + record.quiz.guest_team + '赛事结算出错,现已讲您的奖金' + str(
                    earn_coin) \
                                   + '重新发放,请查收！'
                u_mes.save()


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        start_with = datetime.datetime(2018, 8, 29, 19, 0, 0)
        print(start_with)
        records = Record.objects.filter(open_prize_time__gt=start_with, is_distribution=True, rule__type='0',
                                        earn_coin__lt=0)
        print(len(records))
        process_main(records)
