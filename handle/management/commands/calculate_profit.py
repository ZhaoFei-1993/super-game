# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import datetime
from django.db.models import Q
from quiz.models import Record, ClubProfitAbroad, Quiz
from chat.models import Club
from utils.functions import normalize_fraction


class Command(BaseCommand):
    help = "计算盈利"

    def handle(self, *args, **options):
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')

        yesterday = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                      int(date_last.split('-')[2]), 0, 0)
        today = datetime.datetime(int(date_now.split('-')[0]), int(date_now.split('-')[1]), int(date_now.split('-')[2]),
                                  0, 0)
        print(yesterday)
        print(today)

        quizs = Quiz.objects.filter(status=str(Quiz.BONUS_DISTRIBUTION), begin_at__range=(yesterday, today))
        if len(quizs) > 0:
            quiz_list = []
            for quiz in quizs:
                quiz_list.append(quiz.id)
            print(quiz_list)
            for club in Club.objects.filter(~Q(room_title='HAND俱乐部')):
                robot_platform_sum = 0
                platform_sum = 0
                profit_robot = 0
                profit_user = 0
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

                    profit_table = ClubProfitAbroad()
                    profit_table.roomquiz_id = club.pk
                    profit_table.robot_platform_sum = normalize_fraction(robot_platform_sum, 3)
                    profit_table.platform_sum = normalize_fraction(platform_sum, 3)
                    profit_table.profit = normalize_fraction(profit_user, 3)
                    profit_table.profit_total = normalize_fraction(profit_total, 3)
                    # profit_table.save()

                    print('=======================================>', club.room_title)
                    print('robot_platform_sum = ', normalize_fraction(robot_platform_sum, 3))
                    print('platform_sum = ', normalize_fraction(platform_sum, 3))
                    print('profit_robot = ', normalize_fraction(profit_robot, 3))
                    print('profit_user = ', normalize_fraction(profit_user, 3))
                    print('profit_total = ', normalize_fraction(profit_total, 3))
                    print('----------------------------------------')
