# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from spider.management.commands.stock_result_new import ergodic_record, newobject
from spider.management.commands.stock_index import *
from guess.models import Periods
import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        dt = {'num': '2704.34', 'status': 'up', 'auto': True}
        period = Periods.objects.get(id=234)
        # ergodic_record(period, dt, None)
        print('放出题目')
        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
            next_end += datetime.timedelta(1)
            next_start += datetime.timedelta(1)
        per = int(period.periods) + 1
        newobject(str(per), period.stock_id, next_start, next_end)
        # ---------------------------------------------------------------------------------------

        dt = {'num': '8402.51', 'status': 'up', 'auto': True}
        period = Periods.objects.get(id=235)
        # ergodic_record(period, dt, None)
        print('放出题目')
        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
            next_end += datetime.timedelta(1)
            next_start += datetime.timedelta(1)
        per = int(period.periods) + 1
        newobject(str(per), period.stock_id, next_start, next_end)
        # ---------------------------------------------------------------------------------------

        dt = {'num': '27243.85', 'status': 'up', 'auto': True}
        period = Periods.objects.get(id=236)
        # ergodic_record(period, dt, None)
        print('放出题目')
        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + market_hk_start_time[0],
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
            next_end += datetime.timedelta(1)
            next_start += datetime.timedelta(1)
        per = int(period.periods) + 1
        newobject(str(per), period.stock_id, next_start, next_end)
        # ---------------------------------------------------------------------------------------
