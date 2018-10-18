# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from django.core.management import call_command


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # for i in range(200):
        #     call_command('stock_recording')

        from marksix.models import MarkSixBetLimit
        for id in [100, 101]:
            for i in MarkSixBetLimit.objects.filter(options_id=99):
                mark_six_betlimit = MarkSixBetLimit()
                mark_six_betlimit.max_limit = i.max_limit
                mark_six_betlimit.min_limit = i.min_limit
                mark_six_betlimit.club_id = i.club_id
                mark_six_betlimit.options_id = id
                mark_six_betlimit.save()


















