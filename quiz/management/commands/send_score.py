# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score
from local_settings import CHANNEL_LAYERS


class Command(BaseCommand):
    help = "推送竞猜比分"

    def handle(self, *args, **options):
        config = CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        host, port = config

        redis_conn = Redis(host, port)
        q = Queue(connection=redis_conn)
        q.enqueue(quiz_send_score, 1660, 1, 2)
