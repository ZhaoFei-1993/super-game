# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from django.core.management import call_command
from quiz.models import *


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # for i in range(200):
        #     call_command('stock_recording')

        # from utils.functions import normalize_fraction
        # from decimal import Decimal
        # a = Decimal('120.12130000000')
        # print(normalize_fraction(a, 8))

        # import datetime
        # import time
        # a = (datetime.datetime.now() + datetime.timedelta(minutes=5)) - datetime.datetime.now()
        # b = datetime.datetime.now()
        # print(int((a - b).total_seconds()))
        # print(int(time.time()))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        import requests
        from bs4 import BeautifulSoup
        # url = 'https://www.lotto-8.com/listltohk.asp'
        # response = requests.get(url=url, headers=headers)
        # soup = BeautifulSoup(response.text, 'lxml')
        # for td_tag in soup.select('table[class="auto-style4"]')[0].find_all('tr')[1:5]:
        #     now_open_oth_ymd = td_tag.find_all('td')[0].text.replace('/', '-')
        #     print(now_open_oth_ymd)
        #
        #     next_open_oth_ymd = td_tag.find_all('td')[3].text.replace('/', '-')
        #     print(next_open_oth_ymd)



        # import datetime
        # now_time = datetime.datetime.now()
        # last_time = datetime.datetime.now() + datetime.timedelta(minutes=4, seconds=31)
        # a = last_time - now_time
        # print(now_time.timetuple())

        from utils.cache import get_cache, set_cache
        set_cache('record_stock_bet_count_' + '395', {'rise': 0, 'fall': 0})
        set_cache('record_stock_bet_count_' + '396', {'rise': 0, 'fall': 0})
        set_cache('record_stock_bet_count_' + '397', {'rise': 0, 'fall': 0})
        set_cache('record_stock_bet_count_' + '398', {'rise': 0, 'fall': 0})















