# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from promotion.models import UserPresentation, PromotionRecord
import datetime
from decimal import Decimal
from users.models import UserInvitation
from quiz.models import Quiz, Record


class Command(BaseCommand):
    help = "fix_user_promotions"

    def handle(self, *args, **options):
        print('Go Time')

        print('================ 处理异常数据 ================')
        record_id_list = PromotionRecord.objects.filter(status=2).values_list('record_id', flat=True)
        quiz_id_list = Record.objects.filter(id__in=record_id_list).values_list('quiz_id', flat=True)
        quiz_status_map = {}
        for quiz in Quiz.objects.filter(id__in=quiz_id_list):
            quiz_status_map.update({quiz.id: int(quiz.status)})

        for record in PromotionRecord.objects.filter(status=2):
            quiz_id = Record.objects.filter(id=record.record_id).values_list('quiz_id', flat=True)[0]
            if quiz_status_map[quiz_id] != Quiz.DELAY:
                record.status = 1
                record.save()
        print('================ 处理异常数据处理完毕 ================')
        #
        # begin_time = datetime.datetime.strptime('2018-10-18 00:00:00', '%Y-%m-%d %H:%M:%S')
        # records = PromotionRecord.objects.filter(created_at__gt=begin_time, status=1)
        # print('共', len(records), '条')
        #
        # for record in records:
        #     source = record.source
        #     # 用户ID
        #     user_id = record.user_id
        #
        #     # 俱乐部ID
        #     if source == 1 or source == 2:
        #         club_id = record.roomquiz_id
        #     else:
        #         club_id = record.club_id
        #
        #     # 下注流水
        #     if source == 1 or source == 2:
        #         bet = record.bet
        #     elif source == 3:
        #         bet = record.bet_coin
        #     else:
        #         bet = record.bets
        #
        #     # 盈亏
        #     if record.earn_coin > 0:
        #         income = record.earn_coin - bet
        #     else:
        #         income = record.earn_coin
        #     # 转化为str避免失精
        #     bet = str(bet)
        #     income = str(income)
        #
        #     my_inviter = UserInvitation.objects.filter(~Q(inviter_type=2), invitee_one=user_id).first()
        #     if my_inviter is not None:
        #         created_at_day = record.created_at.strftime('%Y-%m-%d')  # 当天日期
        #         created_at = str(created_at_day) + ' 00:00:00'  # 创建时间
        #         data_number = UserPresentation.filter(club_id=club_id, user_id=my_inviter.inviter.id,
        #                                               created_at=created_at).count()
        #         if data_number > 0:
        #             day_data = UserPresentation.get(club_id=club_id, user_id=my_inviter.inviter.id,
        #                                             created_at=created_at)
        #             day_data.bet_water += Decimal(bet)
        #             day_data.dividend_water += Decimal(bet) * Decimal('0.005')
        #             day_data.income += Decimal(income)
        #             day_data.save()
        #         else:
        #             day_data = UserPresentation()
        #             day_data.user_id = my_inviter.inviter.id
        #             day_data.club_id = club_id
        #             day_data.bet_water = Decimal(bet)
        #             day_data.dividend_water = Decimal(bet) * Decimal('0.005')
        #             day_data.income = Decimal(income)
        #             day_data.created_at = created_at
        #             day_data.save()
        print('End Time')
