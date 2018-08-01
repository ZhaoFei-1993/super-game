# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.eth import *
from time import time
from base.app import BaseView
from utils.cache import get_cache, set_cache
from console.consumers.eth_blocknum import consumer_ethblock
from redis import Redis
from rq import Queue
import local_settings


class Command(BaseCommand, BaseView):
    help = "获取ETH_blocknum"
    cacheKey = 'pre_eth_block_num'

    def add_arguments(self, parser):
        parser.add_argument('blocknum', type=str)

    def handle(self, *args, **options):
        param_blocknum = int(options['blocknum'])

        # redis_conn = Redis()
        # q = Queue(connection=redis_conn)
        # q.enqueue(consumer_ethblock, param_blocknum)
        # raise CommandError('param_blocknum = ', param_blocknum)

        start_time = time()
        if param_blocknum != 0:
            set_cache(self.cacheKey, param_blocknum, 86400)

        eth_wallet = Wallet()
        obj = eth_wallet.get(url='v1/account/gethightblock')
        content = int(obj['data']['blocknum'])

        # print('获取到block:', content)
        if not content:
            raise CommandError('获取blocknum失败')

        cache_block_height = get_cache(self.cacheKey)
        if cache_block_height is None:
            cache_block_height = content

        cache_blocknum = int(cache_block_height)

        if cache_blocknum is None:
            raise CommandError('首次运行设置blocknum')

        print('cache_blocknum:', cache_blocknum)
        # 缓存中blocknum
        if cache_blocknum < content:
            set_cache(self.cacheKey, content, 86400)
            print('content:', content)
            for block_number in range(cache_blocknum, content):
                # 消息队列
                config = local_settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
                host, port = config
                redis_conn = Redis(host, port)
                q = Queue(connection=redis_conn)
                q = Queue(connection=redis_conn)
                q.enqueue(consumer_ethblock, block_number)

        stop_time = time()

        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
