# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from rq import Connection, Worker, use_connection
from redis import Redis
import local_settings


class Command(BaseCommand):
    help = "RedisQueue队列命令"

    def handle(self, *args, **options):
        config = local_settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        host, port = config

        with Connection():
            qs = args[1:] or ['default']

            redis_conn = Redis(host, port)
            use_connection(redis_conn)
            w = Worker(qs)
            w.work()

