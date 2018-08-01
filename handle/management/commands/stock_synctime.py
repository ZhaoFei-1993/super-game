# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Periods
from guess.consumers import confirm_period
from rq import Queue
from redis import Redis
import datetime


class Command(BaseCommand):
    help = "推送股指封盘状态"

    def handle(self, *args, **options):
        redis_conn = Redis()
        q = Queue(connection=redis_conn)

        periods = Periods.objects.filter(is_result=False)
        for period in periods:
            # period_id = period.id
            # is_seal = period.is_seal
            # now_time = datetime.datetime.now()
            # end_time = period.rotary_header_time + datetime.timedelta(minutes=5)
            # if period.is_seal is True and end_time > now_time:
            #     q.enqueue(confirm_period, period_id, is_seal)
            q.enqueue(confirm_period, 133, True)
