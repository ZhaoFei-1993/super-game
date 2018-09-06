# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from spider.management.commands.stock_result_new import ergodic_record
from guess.models import Periods


class Command(BaseCommand):

    def handle(self, *args, **options):
        dt = {'num': '2704.34', 'status': 'up'}
        period = Periods.objects.get(id=234)
        ergodic_record(period, dt, None)

        dt = {'num': '8402.51', 'status': 'up'}
        period = Periods.objects.get(id=235)
        ergodic_record(period, dt, None)

        dt = {'num': '27243.85', 'status': 'up'}
        period = Periods.objects.get(id=236)
        ergodic_record(period, dt, None)
