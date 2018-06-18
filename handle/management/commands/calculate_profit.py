# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import datetime
from django.db.models import Q
from quiz.models import Record, ClubProfitAbroad, Quiz, CashBackLog
from chat.models import Club
from users.models import CoinPrice
from utils.functions import normalize_fraction


class Command(BaseCommand):
    help = "计算盈利--昨天"

    def handle(self, *args, **options):
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        start_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                       int(date_last.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                     int(date_last.split('-')[2]), 23, 59, 59)
        print(start_with)
        print(end_with)

        quizs = Quiz.objects.filter(status=str(Quiz.BONUS_DISTRIBUTION), begin_at__range=(start_with, end_with))
        if len(quizs) > 0:
            quiz_list = []
            for quiz in quizs:
                quiz_list.append(quiz.id)
            print(quiz_list)
            for club in Club.objects.filter(~Q(room_title='HAND俱乐部')):
                coin_price = CoinPrice.objects.get(coin_name=club.room_title[:-3])
                robot_platform_sum = 0
                platform_sum = 0
                profit_robot = 0
                profit_user = 0
                cash_back_sum = 0
                records = Record.objects.filter(roomquiz_id=club.id, is_distribution=True, quiz__id__in=quiz_list)
                if len(records) > 0:
                    for record in records:
                        if record.user.is_robot is True:
                            robot_platform_sum = robot_platform_sum + record.bet
                            if record.earn_coin > 0:
                                profit_robot = profit_robot + (record.earn_coin - record.bet)
                            else:
                                profit_robot = profit_robot + record.earn_coin
                        else:
                            platform_sum = platform_sum + record.bet
                            if record.earn_coin > 0:
                                profit_user = profit_user + (record.earn_coin - record.bet)
                            else:
                                profit_user = profit_user + record.earn_coin

                    if profit_robot <= 0:
                        profit_robot = abs(profit_robot)
                    else:
                        profit_robot = float('-' + str(profit_robot))

                    if profit_user <= 0:
                        profit_user = abs(profit_user)
                    else:
                        profit_user = float('-' + str(profit_user))

                    profit_total = float(profit_user) + float(profit_robot)

                    for cash_back_log in CashBackLog.objects.filter(roomquiz_id=club.id, quiz__id__in=quiz_list):
                        cash_back_sum = float(cash_back_sum) + float(cash_back_log.cash_back_sum)

                    profit_table = ClubProfitAbroad()
                    profit_table.roomquiz_id = club.pk

                    profit_table.robot_platform_sum = normalize_fraction(robot_platform_sum, 3)
                    profit_table.robot_platform_rmb = normalize_fraction(
                        float(robot_platform_sum) * float(coin_price.price), 8)

                    profit_table.platform_sum = normalize_fraction(platform_sum, 3)
                    profit_table.platform_rmb = normalize_fraction(float(platform_sum) * float(coin_price.price), 8)

                    profit_table.profit = normalize_fraction(profit_user, 3)
                    profit_table.profit_rmb = normalize_fraction(float(profit_user) * float(coin_price.price), 8)

                    profit_table.profit_total = normalize_fraction(profit_total, 3)
                    profit_table.profit_total_rmb = normalize_fraction(float(profit_total) * float(coin_price.price), 8)

                    profit_table.cash_back_sum = normalize_fraction(cash_back_sum, 2)
                    profit_table.save()
                    profit_table.created_at = end_with
                    profit_table.save()

                    print('=======================================>', club.room_title)
                    print('robot_platform_sum = ', normalize_fraction(robot_platform_sum, 3))
                    print('robot_platform_rmb = ',
                          normalize_fraction(float(robot_platform_sum) * float(coin_price.price), 8))

                    print('platform_sum = ', normalize_fraction(platform_sum, 3))
                    print('platform_rmb = ', normalize_fraction(float(platform_sum) * float(coin_price.price), 8))

                    print('profit_robot = ', normalize_fraction(profit_robot, 3))
                    print('profit_user = ', normalize_fraction(profit_user, 3))
                    print('profit_rmb = ', normalize_fraction(float(profit_user) * float(coin_price.price), 8))

                    print('profit_total = ', normalize_fraction(profit_total, 3))
                    print('profit_total_rmb', normalize_fraction(float(profit_total) * float(coin_price.price), 8))

                    print('cash_back_sum = ', normalize_fraction(cash_back_sum, 2))
                    print('----------------------------------------')
                else:
                    profit_table = ClubProfitAbroad()
                    profit_table.roomquiz_id = club.id
                    profit_table.save()
                    profit_table.created_at = end_with
                    profit_table.save()
