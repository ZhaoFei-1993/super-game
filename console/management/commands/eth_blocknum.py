# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.eth import *
from time import time
from base.app import BaseView
from utils.cache import get_cache, set_cache, redis_lpush


class Command(BaseCommand, BaseView):
    help = "获取ETH_blocknum"
    cacheKey = 'pre_eth_block_num'
    listKey = 'pre_eth_block_list'

    def add_arguments(self, parser):
        parser.add_argument('blocknum', type=str)

    def handle(self, *args, **options):
        param_blocknum = int(options['blocknum'])  # 从参数中传进
        if param_blocknum != 0:
            set_cache(self.cacheKey, param_blocknum, 86400)

        eth_wallet = Wallet()
        start_time = time()
        obj = eth_wallet.get(url='/api/v1/account/gethightblock')
        content = obj['data']['blocknum']
        print('获取到block:', content)
        if not content:
            raise CommandError('获取blocknum失败')

        cache_blocknum = get_cache(self.cacheKey)

        if cache_blocknum is None:
            cache_blocknum = 1

        print('cache_blocknum:', cache_blocknum)
        # 缓存中blocknum
        if cache_blocknum < content:
            set_cache(self.cacheKey, content, 86400)
            print('content:', content)
            for i in range(int(cache_blocknum), int(content)):
                redis_lpush(self.listKey, i)

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
