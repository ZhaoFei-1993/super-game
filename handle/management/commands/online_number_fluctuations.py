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
        now_number_key = "NOW_INITIAL_ONLINE_USER_" + str(day)       # 在线人数key
        number_key = "INITIAL_ONLINE_USER_" + str(day)       # 在线人数key
        lists = get_cache(now_number_key)
        for list in lists:
            for i in list:
                list_i = list[i]
                for s in list_i:
                    calculation_one = int(random.randint(1, 2))
                    if calculation_one == 1:
                        list_i[s]['quiz'] = int(list_i[s]['quiz']) + fluctuation
                    else:
                        list_i[s]['quiz'] = int(list_i[s]['quiz']) - fluctuation
                    calculation_two = int(random.randint(1, 2))
                    if calculation_two == 1:
                        list_i[s]['guess'] = int(list_i[s]['guess']) + fluctuation
                    else:
                        list_i[s]['guess'] = int(list_i[s]['guess']) - fluctuation
        set_cache(number_key, lists, 24 * 3600)
        print("人数波动已经完成！")