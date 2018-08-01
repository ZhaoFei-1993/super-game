# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import random
from datetime import datetime, timedelta
from utils.cache import get_cache, set_cache


class Command(BaseCommand):
    help = "在线人数波动"

    def handle(self, *args, **options):
        day = datetime.now().strftime('%Y-%m-%d')
        fluctuation = int(random.randint(1, 5))       # 波动人数
        number_key = "INITIAL_ONLINE_USER_" + str(day)       # 在线人数key
        # fluctuation_key = "ONLINE_NUMBER_FLUCTUATIONS_" + str(day)    # 波动时间key
        lists = get_cache(number_key)
        # fluctuation_setting = get_cache(fluctuation_key)
        # if fluctuation_setting == None or fluctuation_setting == "":
        for list in lists:
            for i in list:
                calculation_one = int(random.randint(1, 2))
                if calculation_one == 1:
                    i['quiz'] = int(i['quiz']) + fluctuation
                else:
                    i['quiz'] = int(i['quiz']) - fluctuation
                calculation_two = int(random.randint(1, 2))
                if calculation_two == 1:
                    i['guess'] = int(i['guess']) + fluctuation
                else:
                    i['guess'] = int(i['guess']) - fluctuation
        set_cache(number_key, lists, 24 * 3600)