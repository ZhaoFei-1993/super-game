# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Issues, Periods
from guess.consumers import guess_pk_detail, guess_pk_result_list
from guess.consumers import guess_graph

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Connection': 'close',
}


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        index_list = ['1234.71', '1298.71', '1245.70', '1567.70', '1111.70']
        guess_graph(178, index_list)
        guess_graph(179, list(reversed(index_list)))
        print('成功')





