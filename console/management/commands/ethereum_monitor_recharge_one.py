# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.app import BaseView
from console.consumers.ethereum_monitor_recharge import etheruem_monitor
from redis import Redis
from rq import Queue
import local_settings


class Command(BaseCommand, BaseView):
    help = "监控以太坊充值数据"

    def add_arguments(self, parser):
        parser.add_argument('block_height', type=str)

    def handle(self, *args, **options):
        block_height = int(options['block_height'])

        config = local_settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        host, port = config
        redis_conn = Redis(host, port)
        q = Queue(connection=redis_conn)
        q.enqueue(etheruem_monitor, block_height)

        self.stdout.write(self.style.SUCCESS('done'))
