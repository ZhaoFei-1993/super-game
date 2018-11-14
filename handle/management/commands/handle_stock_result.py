# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from spider.management.commands.stock_result_new import GuessRecording
from spider.management.commands.stock_index_new import StockIndex
from guess.models import Periods
import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        # dt = {'num': '2583.46', 'status': 'up', 'auto': True}
        # period = Periods.objects.get(id=339)
        # # ergodic_record(period, dt, datetime.datetime.strptime('2018-10-11 23:59:59', '%Y-%m-%d %H:%M:%S'))
        #
        # print('放出题目')
        # open_date = period.lottery_time.strftime('%Y-%m-%d')
        # next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
        #                                         '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
        #                                       '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
        #     next_end += datetime.timedelta(1)
        #     next_start += datetime.timedelta(1)
        # per = int(period.periods) + 1
        # newobject(str(per), period.stock_id, next_start, next_end)

        # # ---------------------------------------------------------------------------------------
        #
        # dt = {'num': '7524.09', 'status': 'up', 'auto': True}
        # period = Periods.objects.get(id=340)
        # # ergodic_record(period, dt, datetime.datetime.strptime('2018-10-11 23:59:59', '%Y-%m-%d %H:%M:%S'))
        # print('放出题目')
        # open_date = period.lottery_time.strftime('%Y-%m-%d')
        # next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
        #                                         '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
        #                                       '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
        #     next_end += datetime.timedelta(1)
        #     next_start += datetime.timedelta(1)
        # per = int(period.periods) + 1
        # newobject(str(per), period.stock_id, next_start, next_end)

        # ---------------------------------------------------------------------------------------

        # dt = {'num': '7329.06', 'status': 'down', 'auto': True}
        # period = Periods.objects.get(id=334)
        # ergodic_record(period, dt, datetime.datetime.strptime('2018-10-12 23:59:59', '%Y-%m-%d %H:%M:%S'))
        # print('放出题目')
        # open_date = period.lottery_time.strftime('%Y-%m-%d')
        # next_start = datetime.datetime.strptime(open_date + ' ' + market_en_start_time[0],
        #                                         '%Y-%m-%d %H:%M:%S')
        # next_end = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0],
        #                                       '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # while (next_end - datetime.timedelta(hours=12)).isoweekday() >= 6 or (
        #         next_end - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in market_en_end_time:
        #     next_end += datetime.timedelta(1)
        #     next_start += datetime.timedelta(1)
        # per = int(period.periods) + 1
        # newobject(str(per), period.stock_id, next_start, next_end)

        # ---------------------------------------------------------------------------------------

        # dt = {'num': '25052.83', 'status': 'down', 'auto': True}
        # period = Periods.objects.get(id=335)
        # ergodic_record(period, dt, datetime.datetime.strptime('2018-10-12 23:59:59', '%Y-%m-%d %H:%M:%S'))
        # print('放出题目')
        # open_date = period.lottery_time.strftime('%Y-%m-%d')
        # next_start = datetime.datetime.strptime(open_date + ' ' + market_en_start_time[0],
        #                                         '%Y-%m-%d %H:%M:%S')
        # next_end = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0],
        #                                       '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        # while (next_end - datetime.timedelta(hours=12)).isoweekday() >= 6 or (
        #         next_end - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in market_en_end_time:
        #     next_end += datetime.timedelta(1)
        #     next_start += datetime.timedelta(1)
        # per = int(period.periods) + 1
        # newobject(str(per), period.stock_id, next_start, next_end)

        # ---------------------------------------------------------------------------------------
        guess_recording = GuessRecording()
        stock_index = StockIndex()
        dt = {'num': '25792.87', 'status': 'up', 'auto': True}
        period = Periods.objects.get(id=451)
        date_day = datetime.datetime.strptime(period.lottery_time.strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                              "%Y-%m-%d %H:%M:%S")
        guess_recording.take_result(period, dt, date_day)
        guess_recording.ergodic_record(period, dt, None)
        print('放出题目')
        stock_index.new_period(period)
        # # ---------------------------------------------------------------------------------------
