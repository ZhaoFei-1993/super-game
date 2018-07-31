# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import re
import datetime
from guess.models import Periods
from django.db.models import Q, Sum, Max
from spider.management.commands.stock_result import ergodic_record, newobject


market_rest_cn_list = ['2018-06-18', '2018-09-24', '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04', '2018-10-05']
market_rest_en_dic = ['2018-09-03', '2018-11-22', '2018-12-25']
market_rese_hk_dic = ['2018-09-25', '2018-10-01', '2018-10-17', '2018-12-25', '2018-12-26']

market_rest_cn_start_time = ['09:30:00']
market_hk_start_time = ['09:30:00']
market_en_start_time = ['21:30:00']

market_rest_cn_end_time = ['15:00:00']
market_hk_end_time = ['16:10:00']
market_en_end_time = ['04:00:00']


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # periods_sum = Periods.objects.all().aggregate(Sum('id'), Sum('periods'))
        # print(periods_sum)
        # print(type(periods_sum['id__sum']))
        # print(float(periods_sum['id__sum']))

        period = Periods.objects.get(pk=126)
        dt = {'num': '9174.83', 'status': 'down', 'auto': True}
        date = datetime.datetime.now()
        ergodic_record(period, dt, date)
        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
            next_end += datetime.timedelta(1)
        per = int(period.periods) + 1
        newobject(str(per), period.stock_id, next_start, next_end)

        period = Periods.objects.get(pk=128)
        dt = {'num': '28574.64', 'status': 'down', 'auto': True}
        date = datetime.datetime.now()
        ergodic_record(period, dt, date)
        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + market_hk_start_time[0],
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
            next_end += datetime.timedelta(1)
        per = int(period.periods) + 1
        newobject(str(per), period.stock_id, next_start, next_end)




