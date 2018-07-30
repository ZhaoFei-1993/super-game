# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import re
import datetime
from guess.models import Periods
from django.db.models import Q, Sum, Max
from spider.management.commands.stock_result import ergodic_record


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # periods_sum = Periods.objects.all().aggregate(Sum('id'), Sum('periods'))
        # print(periods_sum)
        # print(type(periods_sum['id__sum']))
        # print(float(periods_sum['id__sum']))

        periods = Periods.objects.get(pk=125)
        dt = {'num': '28733.13', 'status': 'down', 'auto': True}
        date = datetime.datetime.now()
        ergodic_record(periods, dt, date)




