# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record, EveryDayInjectionValue
from users.models import CoinPrice, User
from chat.models import Club
from utils.functions import normalize_fraction
import datetime


class Command(BaseCommand):
    help = "计算现在用户单日投注总量"

    def handle(self, *args, **options):
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        start_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                       int(date_last.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                     int(date_last.split('-')[2]), 23, 59, 59)
        print(date_last, start_with, end_with, sep='\n')

        user_list = []
        records = Record.objects.filter(created_at__range=(start_with, end_with))
        for record in records:
            if record.user_id not in user_list:
                user_list.append(record.user_id)

        print(user_list)
        for user_id in user_list:
            record_sum = 0
            for record_personal in records.filter(user_id=user_id):
                club_name = Club.objects.get(pk=record_personal.roomquiz_id).room_title
                coin_price = CoinPrice.objects.get(coin_name=club_name.replace('俱乐部', ''))
                record_sum = record_sum + record_personal.bet * coin_price.price

            print(user_id, ' ========= ', record_sum)
            obj = EveryDayInjectionValue()
            obj.user_id = user_id
            obj.injection_value = normalize_fraction(record_sum, 8)
            obj.is_robot = User.objects.get(pk=user_id).is_robot
            obj.injection_time = date_last
            obj.save()
