# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.app import BaseView
from utils.cache import get_cache, set_cache
from redis import Redis
from rq import Queue, use_connection
from base.function import curl_get
from console.consumers.eth_monitor import etheruem_monitor, get_api_url
import local_settings


class Command(BaseCommand, BaseView):
    help = "ETH币充值监控"
    cacheKey = 'key_eth_block_height'
    coin = 'ETH'

    def add_arguments(self, parser):
        parser.add_argument('--block_height', type=int, help='块高度')
        parser.add_argument('--only_one_block', type=int, help='是否只获取一个块高度')

    def set_queue(self, block_height):
        """
        写入消息队列
        :param block_height:
        :return:
        """
        config = local_settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        host, port = config

        redis_conn = Redis(host, port)
        q = Queue(connection=redis_conn)
        q.enqueue(etheruem_monitor, block_height)

        self.stdout.write(self.style.SUCCESS('监控高度=' + str(block_height) + '的' + self.coin + '充值数据'))

    @staticmethod
    def get_block_height():
        """
        获取区块链上最大节点高度
        :return:
        """
        try:
            response = curl_get(url=get_api_url('eth_blockNumber'))
            block_height = int(response['result'], 0)
        except Exception:
            raise CommandError('获取区块链最新节点高度失败')

        return block_height

    def handle(self, *args, **options):
        chain_block_height = self.get_block_height()

        if options['block_height']:
            block_height = options['block_height']
        else:
            block_height = chain_block_height

        # 只监控某个块高度数据
        if options['only_one_block']:
            self.set_queue(block_height)
            raise CommandError('')

        # 获取缓存中的块高度值，若缓存未设置，则首次设置的值为当前区块链块高
        cache_block_height = get_cache(self.cacheKey)
        if cache_block_height is None:
            cache_block_height = block_height
            set_cache(self.cacheKey, chain_block_height)

        # 当缓存中的块高度值大于参数传过来的高度值，则重新写入缓存中的块高度值为参数指定的高度值
        # 如缓存中块高为123，参数传100，区块链上高度为125，则会监控100~125间的所有块数据
        if cache_block_height > chain_block_height:
            set_cache(self.cacheKey, block_height)

        cache_block_height = int(cache_block_height)
        for block in range(cache_block_height, chain_block_height + 1):
            self.set_queue(block)

        set_cache(self.cacheKey, chain_block_height)
        self.stdout.write(self.style.SUCCESS('ok'))
