# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import datetime
from django.db.models import Q
from quiz.models import Record, ClubProfitAbroad, Quiz, CashBackLog
from chat.models import Club
from users.models import CoinPrice
from quiz.models import EveryDayInjectionValue
from utils.functions import normalize_fraction


class Command(BaseCommand):
    help = "计算返现--昨天"

    def handle(self, *args, **options):
        # 分配给真实用户的比例
        rate = 0.1

        # 划分出时间区间
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        start_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                       int(date_last.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                     int(date_last.split('-')[2]), 23, 59, 59)
        print(date_last, start_with, end_with, sep='\n')

        # 返现金额上限
        cash_bcak_pool = normalize_fraction(30000000 / (365 * 3), 2)
        print('返现池金额 = ', cash_bcak_pool)

        # 计算时间区间内总投注量（rmb）
        platform_sum = 0  # 包含机器人（rmb）
        for dt in EveryDayInjectionValue.objects.filter(injection_time=date_last):
            platform_sum = float(platform_sum) + float(dt.injection_value)
        print('总的投注量(rmb) = ', platform_sum)

        for dt in EveryDayInjectionValue.objects.filter(injection_time=date_last):
            if dt.is_robot is True:
                gsg_cash_back = float(cash_bcak_pool) * (1 - rate) * (float(dt.injection_value)/float(platform_sum))
            else:
                gsg_cash_back = float(cash_bcak_pool) * rate * (float(dt.injection_value) / float(platform_sum))
            gsg_cash_back = normalize_fraction(gsg_cash_back, 2)
            dt.cash_back_gsg = gsg_cash_back
            dt.save()

        # # 计算时间区间内总投注量（rmb）
        # platform_sum = 0  # 包含机器人（rmb）
        # for profit_abroad in ClubProfitAbroad.objects.filter(created_at__range=(start_with, end_with)):
        #     platform_sum = float(platform_sum) + float(profit_abroad.robot_platform_rmb) + float(
        #         profit_abroad.platform_rmb)
        # print('总的投注量(rmb) = ', platform_sum)
        #
        # # 分配个人返现
        # user_list = []
        # records = Record.objects.filter(~Q(roomquiz_id=Club.objects.get(room_title='HAND俱乐部').id), is_distribution=True,
        #                                 open_prize_time__range=(start_with, end_with))
        # if len(records) > 0:
        #     for record in records:
        #         if record.user.id in user_list:
        #             pass
        #         else:
        #             user_list.append(record.user.id)
        #             user_bet_sum = 0  # 个人今日投注总额
        #             for record_personal in records.filter(user_id=record.user.id):
        #                 coin_price = CoinPrice.objects.get(
        #                     coin_name=Club.objects.get(pk=record_personal.roomquiz_id).room_title[:-3])
        #                 user_bet_sum = float(user_bet_sum) + (float(record_personal.bet) * float(coin_price.price))
        #             gsg_cash_back = (float(user_bet_sum) / float(platform_sum)) * float(cash_bcak_pool)
        #             gsg_cash_back = normalize_fraction(gsg_cash_back, 2)
        #             print('user_id = ', record.user.id, ' , 总投注量： ', user_bet_sum, ' ,返现的gsg： ', gsg_cash_back)
