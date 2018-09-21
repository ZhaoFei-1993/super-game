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
        left_index_dic = {'15:01': '8460.18', '15:02': '8422.18', '15:03': '8433.18', '15:04': '8444.18',
                          '15:05': '8499.18', }

        right_index_dic = {'15:01': '2755.49', '15:02': '2722.18', '15:03': '2744.18', '15:04': '2766.18',
                           '15:05': '2799.18', }

        guess_graph(178, left_index_dic)
        guess_graph(179, right_index_dic)
        print('成功')





