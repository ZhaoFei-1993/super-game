# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score


class Command(BaseCommand):
    help = "推送竞猜比分"

    def handle(self, *args, **options):
        quiz_id = 1660
        host = 1
        guest = 2

        redis_conn = Redis()
        q = Queue(connection=redis_conn)
        q.enqueue(quiz_send_score, quiz_id, host, guest)
