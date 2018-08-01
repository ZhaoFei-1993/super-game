# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from rq import Connection, Worker
from redis import Redis


class Command(BaseCommand):
    help = "RedisQueue队列命令"

    def handle(self, *args, **options):
        with Connection():
            qs = args[1:] or ['default']

            redis_conn = Redis()
            w = Worker(qs, connection=redis_conn)
            w.work()

