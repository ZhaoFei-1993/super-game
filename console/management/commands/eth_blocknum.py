# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time as format_time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *
from time import time
import math
import json
import os
from django.conf import settings
#from django_redis import get_redis_connection
from redis import Redis
from base.app import BaseView
#base_url = "http://127.0.0.1:3001/api/v1/account/gethightblock"

class Command(BaseCommand,BaseView):
    help = "获取ETH_blocknum"
    cacheKey = 'pre_eth_block_num'
    listKey = 'pre_eth_block_list'

    def add_arguments(self, parser):
        parser.add_argument('blocknum', type=str)

    #python manage.py eth_blocknum 0
    #:param blocknum  default=0
    def handle(self, *args, **options):
        redis_obj = Redis()
        param_blocknum = int(options['blocknum'])  #从参数中传进
        if param_blocknum != 0:
            redis_obj.set(self.cacheKey, param_blocknum, 86400)

        eth_wallet = Wallet()
        #raise CommandError('name' + '无效')
        start_time = time()
        #obj = json.loads(response.text)
        obj = eth_wallet.get(url='/api/v1/account/gethightblock')
        content = obj['data']['blocknum']
        print('获取到block:',content)
        if not content:
            print("获取blocknum失败")
            return

        os.chdir(settings.BASE_DIR + '/cache')

        # with open('block_num.txt', 'w+') as f:
        #     datas = f.write(str(content) + "")
        #
        # f.close()

        cache_blocknum = int(redis_obj.get(self.cacheKey).decode('utf-8'))
        #缓存中blocknum
        if cache_blocknum < content:
            redis_obj.set(self.cacheKey, content, 86400)
            for i in range(cache_blocknum,content):
                redis_obj.lpush(self.listKey, i)

        #print(cache_blocknum)

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))



