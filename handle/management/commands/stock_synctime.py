# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Periods
from guess.consumers import confirm_period
from rq import Queue
from redis import Redis


class Command(BaseCommand):
    help = "推送股指封盘状态"

    def add_arguments(self, parser):
        parser.add_argument('period_id', type=str)

    def handle(self, *args, **options):
        redis_conn = Redis()
        q = Queue(connection=redis_conn)

        period_id = int(options['period_id'])
        period = Periods.objects.get(pk=period_id)
        if period.is_seal is True:
            is_seal = period.is_seal
            q.enqueue(confirm_period, period_id, is_seal)
