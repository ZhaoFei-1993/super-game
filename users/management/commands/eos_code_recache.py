# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue
from users.consumers import recache_eos_code


class Command(BaseCommand):
    """
    重新生成eos充值码缓存
    每日随机抽取指定条数记录，凌晨2点重置数据
    """
    help = "重新生成EOS充值码缓存"

    def handle(self, *args, **options):
        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        q.enqueue(recache_eos_code)
