# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.eth import *
from time import time
from base.app import BaseView
from utils.cache import get_cache, set_cache
from console.consumers import *
from redis import Redis
from rq import Queue
from base.function import curl_get

class Command(BaseCommand, BaseView):
    help = "获取coin_blocknum"
    cacheKey = 'pre_xxx_block_num'

    def add_arguments(self, parser):
        parser.add_argument('coin', type=str)
        parser.add_argument('blocknum', type=str)

    def handle(self, *args, **options):
        coin = str(options['coin'])
        param_blocknum = int(options['blocknum'])

        self.cacheKey = self.cacheKey.replace('xxx',coin)

        start_time = time()
        if param_blocknum != 0:
            set_cache(self.cacheKey, param_blocknum, 86400)

        #获取最大blocknum
        obj = curl_get(url='https://blockdozer.com/api/status')
        content = int(obj['info']['blocks'])

        # print('获取到block:', content)
        if not content:
            raise CommandError('获取blocknum失败')

        cache_blocknum = get_cache(self.cacheKey)

        if cache_blocknum is None:
            raise CommandError('首次运行设置blocknum')

        cache_blocknum = int(cache_blocknum)
        print('cache_blocknum:', cache_blocknum)
        # 缓存中blocknum
        if cache_blocknum < content:
            set_cache(self.cacheKey, content, 86400)
            print('content:', content)
            for block_number in range(cache_blocknum, content):
                # 消息队列
                redis_conn = Redis()
                q = Queue(connection=redis_conn)
                func = 'consumer_' + coin + 'block'
                #consumer_bchblock
                q.enqueue(func, block_number)

        stop_time = time()

        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
