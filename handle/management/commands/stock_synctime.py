# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Periods
from guess.consumers import confirm_period
from rq import Queue
from redis import Redis
import datetime
from utils.cache import *


class Command(BaseCommand):
    help = "推送股指封盘状态"

    def handle(self, *args, **options):
        redis_conn = Redis()
        q = Queue(connection=redis_conn)

        periods = Periods.objects.filter(is_result=False)
        for period in periods:
            cache_key = 'period_seal_' + period.id
            if get_cache(cache_key) is None:
                set_cache(cache_key, 0, 86400)
            dt = int(get_cache(cache_key))
            print('cache_key == ', cache_key)
            print('cache_value == ', dt)
            if period.is_seal is True and dt == 0:
                print('推送状态')
                period_status = 1
                q.enqueue(confirm_period, period.id, period_status)
                set_cache(cache_key, period_status, 86400)
                print('推送状态结束')
            elif datetime.datetime.now() > period.lottery_time and dt == 1:
                print('推送状态')
                period_status = 2
                q.enqueue(confirm_period, period.id, period_status)
                set_cache(cache_key, period_status, 86400)
                print('推送状态结束')
        print('----------------------------------------------')

