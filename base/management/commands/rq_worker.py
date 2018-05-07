# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from rq import Connection, Worker


class Command(BaseCommand):
    help = "RedisQueue队列命令"

    def handle(self, *args, **options):
        with Connection():
            qs = args[1:] or ['default']

            w = Worker(qs)
            w.work()

