# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.eth import *
from base.app import BaseView
from utils.cache import get_cache, set_cache
from console.consumers.ethereum_monitor_recharge import etheruem_monitor
from redis import Redis
from rq import Queue
import local_settings


class Command(BaseCommand, BaseView):
    help = "监控以太坊充值数据"
    cacheKey = 'key_ethreum_monitor_recharge'

    def add_arguments(self, parser):
        parser.add_argument('block_height', type=str)

    def handle(self, *args, **options):
        block_height = int(options['block_height'])

        if block_height != 0:
            set_cache(self.cacheKey, block_height)

        eth_wallet = Wallet()
        obj = eth_wallet.get(url='v1/account/gethightblock')
        content = int(obj['data']['blocknum'])

        if not content:
            raise CommandError('获取blocknum失败')

        cache_block_height = get_cache(self.cacheKey)
        if cache_block_height is None:
            cache_block_height = content
            set_cache(self.cacheKey, content)

        cache_blocknum = int(cache_block_height)

        if cache_blocknum is None:
            raise CommandError('首次运行设置blocknum')

        print('cache_blocknum:', cache_blocknum)
        # 缓存中blocknum
        if cache_blocknum < content:
            set_cache(self.cacheKey, content)
            print('content:', content)
            for block_number in range(cache_blocknum, content):
                # 消息队列
                config = local_settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
                host, port = config
                redis_conn = Redis(host, port)
                q = Queue(connection=redis_conn)
                q.enqueue(etheruem_monitor, block_number)

        self.stdout.write(self.style.SUCCESS('done'))
