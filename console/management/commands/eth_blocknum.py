# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.eth import *
from time import time
from redis import Redis
from base.app import BaseView
from utils.cache import get_cache, set_cache

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
            set_cache(self.cacheKey, param_blocknum, 86400)

        eth_wallet = Wallet()
        start_time = time()
        obj = eth_wallet.get(url='/api/v1/account/gethightblock')
        content = obj['data']['blocknum']
        print('获取到block:',content)
        if not content:
            raise CommandError('获取blocknum失败')


        cache_blocknum = get_cache(self.cacheKey)

        if cache_blocknum == None:
            cache_blocknum = 0

        print(cache_blocknum)
        #缓存中blocknum
        if cache_blocknum < content:
            set_cache(self.cacheKey, content, 86400)
            for i in range(cache_blocknum,content):
                redis_obj.lpush(self.listKey, i)

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))



