# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Issues, Periods, Index, Stock
from guess.consumers import guess_pk_detail, guess_pk_result_list
from guess.consumers import guess_graph
import requests
import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Connection': 'close',
}


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # left_index_dic = {'x': ['15:01', '15:02', '15:03', '15:04', '15:05'],
        #                   'y': ['8460.18', '8422.18', '8433.18', '8444.18', '8499.18']}
        #
        # right_index_dic = {'x': ['15:01', '15:02', '15:03', '15:04', '15:05'],
        #                    'y': ['2755.49', '2722.18', '2744.18', '2766.18', '2799.18']}
        #
        # guess_graph(178, left_index_dic)
        # guess_graph(179, right_index_dic)
        # print('成功')

        # url_dji = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d&eprop=minute'
        # url_ndx = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=纳斯达克&hilight=disp_data.*.title&sitesign=12299ccd2e71da74cd27339159e1a3ba&eprop=minute'
        # response = requests.get(url_ndx)
        # data_list = response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['tab']['p'].split(';')[
        #             :-1]
        # data_ymd = data_list[0].split(',')[2].split(' ')[0].replace('/', '-')
        # index_info = []
        # for i in data_list:
        #     info_list = i.split(',')
        #     index_info.append({
        #         'index_time': data_ymd + ' ' + info_list[0],
        #         'index_value': info_list[1],
        #     })
        # print(index_info)

        # title = Stock.STOCK[int(4)][1]
        # print(title)

        print(Stock.STOCK[int('0')][1])

