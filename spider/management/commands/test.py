# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from django.core.management import call_command
from quiz.models import *


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        # for i in range(200):
        #     call_command('stock_recording')

        # from utils.functions import normalize_fraction
        # from decimal import Decimal
        # a = Decimal('120.12130000000')
        # print(normalize_fraction(a, 8))

        # import datetime
        # import time
        # a = (datetime.datetime.now() + datetime.timedelta(minutes=5)) - datetime.datetime.now()
        # b = datetime.datetime.now()
        # print(int((a - b).total_seconds()))
        # print(int(time.time()))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        import requests
        from bs4 import BeautifulSoup
        # url = 'https://www.lotto-8.com/listltohk.asp'
        # response = requests.get(url=url, headers=headers)
        # soup = BeautifulSoup(response.text, 'lxml')
        # for td_tag in soup.select('table[class="auto-style4"]')[0].find_all('tr')[1:5]:
        #     now_open_oth_ymd = td_tag.find_all('td')[0].text.replace('/', '-')
        #     print(now_open_oth_ymd)
        #
        #     next_open_oth_ymd = td_tag.find_all('td')[3].text.replace('/', '-')
        #     print(next_open_oth_ymd)

        # import datetime
        # now_time = datetime.datetime.now()
        # last_time = datetime.datetime.now() + datetime.timedelta(minutes=4, seconds=31)
        # a = last_time - now_time
        # print(now_time.timetuple())

        # from utils.cache import get_cache, set_cache, delete_cache
        # set_cache('record_stock_bet_count_' + '400', {'rise': 0, 'fall': 0})
        # set_cache('record_stock_bet_count_' + '396', {'rise': 0, 'fall': 0})
        # set_cache('record_stock_bet_count_' + '397', {'rise': 0, 'fall': 0})
        # set_cache('record_stock_bet_count_' + '398', {'rise': 0, 'fall': 0})
        #
        # # delete_cache('record_stock_bet_count_' + '394')
        # print('进入脚本')
        # from guess.models import Issues, OptionStockPk
        # if get_cache('record_pk_bet_count' + '_' + str(1)) is None and get_cache(
        #         'record_pk_bet_count' + '_' + str(2)) is None:
        #     set_cache('record_pk_bet_count' + '_' + str(1), {})
        #     set_cache('record_pk_bet_count' + '_' + str(2), {})
        #
        #     for issues in Issues.objects.filter(is_open=0):
        #         key_pk_bet_count = 'record_pk_bet_count' + '_' + str(issues.stock_pk_id)
        #         pk_bet_count = get_cache(key_pk_bet_count)
        #         pk_bet_count.update({issues.id: {}})
        #         for option in OptionStockPk.objects.filter(stock_pk_id=issues.stock_pk_id).order_by('order').values(
        #                 'id'):
        #             pk_bet_count[issues.id].update({option['id']: 0})
        #         set_cache(key_pk_bet_count, pk_bet_count)
        #     print('结束脚本 1')
        #
        # print(get_cache('record_pk_bet_count' + '_' + str(1)))
        # print('---------------------------------------------')
        # print(get_cache('record_pk_bet_count' + '_' + str(2)))
        # print('结束脚本 2')

        # import asyncio
        # import aiohttp
        #
        # async def get_resp(url=None):
        #     print('start to : ', url)
        #     async with aiohttp.ClientSession() as session:
        #         async with session.get(url, verify_ssl=False) as response:
        #             print(response.status)
        #             return await response.text()
        #
        # loop = asyncio.get_event_loop()
        # tasks = [get_resp(url) for url in ['https://www.baidu.com/', 'https://www.google.com/']] + [sleep(5)]
        # loop.run_until_complete(asyncio.wait(tasks))
        # loop.close()
        #
        # 'http://yunhq.sse.com.cn:32041/v1/sh1/line/000001?callback=jQuery111207687464497686252_1541043379848&begin=0&end=-1&select=time%2Cprice%2Cvolume'

        # import asyncio
        # from aiohttp import ClientSession
        #
        # __MUSIC_NUM = 1  # hu 返回的最大歌曲数
        #
        # async def __fetch(url, data, loop):
        #     try:
        #         async with ClientSession(loop=loop) as session:
        #             # hu 发送GET请求，params为GET请求参数，字典类型
        #             async with session.get(url, params=data, timeout=5) as response:
        #                 # hu 以json格式读取响应的body并返回字典类型
        #                 return await response.json()
        #     except Exception as ex:
        #         print('__fetch:%s' % ex)
        #
        # async def getMusicInfo(keyword, offset, loop):
        #     urlFace = 'http://s.music.163.com/search/get'
        #     dataMusic = {'type': '1',
        #                  's': keyword,
        #                  'limit': str(__MUSIC_NUM),
        #                  'offset': str(offset)}
        #     result = None
        #     try:
        #         task = asyncio.ensure_future(__fetch(urlFace, dataMusic, loop), loop=loop)
        #         taskDone = await asyncio.wait_for(task, timeout=5)
        #         if 'result' not in taskDone:
        #             return result
        #
        #         for song in taskDone['result']['songs']:
        #             if result is None:
        #                 result = [{'name': song['name'],
        #                            'artist': song['artists'][0]['name'],
        #                            'picUrl': song['album']['picUrl'],
        #                            'audio': song['audio'],
        #                            'page': song['page']}]
        #             else:
        #                 result.append({'name': song['name'],
        #                                'artist': song['artists'][0]['name'],
        #                                'picUrl': song['album']['picUrl'],
        #                                'audio': song['audio'],
        #                                'page': song['page']})
        #     except Exception as ex:
        #         print('getMusicInfo:%s' % ex)
        #     print('qqqqqqqqqwwwwwwwwwwwwww')
        #     return result
        #
        # def __main():
        #     print('脚本开始')
        #     loop = asyncio.get_event_loop()
        #     music = '彩虹'
        #     player = '周杰伦'
        #     player_1 = '乔楚熙'
        #     task_list = []
        #     task_list.append(asyncio.ensure_future(getMusicInfo(music + player, 1, loop)))
        #     task_list.append(asyncio.ensure_future(getMusicInfo(music + player_1, 1, loop)))
        #     dones, pendings = loop.run_until_complete(asyncio.wait(task_list))
        #     for task in dones:
        #         print(task.result())
        #     # for key, value in taskDone[0].items():
        #     #     print(key + ':' + value)
        #     # for task in task_list:
        #     #     print(task.result())
        #     loop.close()
        #
        # __main()

        import datetime
        import requests
        import re

        url_shen = 'http://www.szse.cn/api/market/ssjjhq/getTimeData?random=0.6430127918854951&marketId=1&code=399001'
        url_shang = 'http://yunhq.sse.com.cn:32041/v1/sh1/line/000001?callback=jQuery111208645993247577721_1541046387829&begin=0&end=-1&select=time%2Cprice%2Cvolume'
        url_djia = 'https://www.nasdaq.com/aspx/IndexData.ashx?index=.indu'
        url_nasdaq = 'https://www.nasdaq.com/aspx/IndexData.ashx?index=ixic'
        url_hsi = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=457e1aa48b5dc5ea25a0766d5d08c047&eprop=minute'

        def get_shang():
            response = requests.get(url_shang, headers=headers, timeout=10)
            resp_json = eval(re.findall('{.*}', response.text)[0])
            begin_time = datetime.datetime.strptime(str(resp_json['date']), '%Y%m%d').strftime('%Y-%m-%d')

            data = resp_json['line']

            data_list = []
            for dt in data:
                index_time_str = begin_time + ' ' + str(dt[0])
                index_time = datetime.datetime.strptime(index_time_str, '%Y-%m-%d %H%M%S')
                index_value = round(dt[1], 2)
                data_list.append([index_time, index_value])

            open_index = data_list[0][1]

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == '15:00:00':
                close_index = data_list[-1][1]

            data_map = {}
            data_map.update(
                {
                    'name': 'shang',
                    'begin_time': begin_time,
                    'open_index': open_index,
                    'data_list': data_list,
                    'close_index': close_index
                }
            )

            print(data_map)

        def get_shen():
            response = requests.get(url_shen, headers=headers, timeout=10)
            resp_json = response.json()
            begin_time = resp_json['datetime'].split(' ')[0]

            open_index = float(resp_json['data']['open'])

            data = resp_json['data']['picupdata']

            data_list = []
            for dt in data:
                index_time_str = begin_time + ' ' + dt[0] + ':00'
                index_time = datetime.datetime.strptime(index_time_str, '%Y-%m-%d %H:%M:%S')
                index_value = float(dt[1])
                data_list.append([index_time, index_value])

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == '15:00:00':
                close_index = data_list[-1][1]

            data_map = {}
            data_map.update(
                {
                    'name': 'shen',
                    'begin_time': begin_time,
                    'open_index': open_index,
                    'data_list': data_list,
                    'close_index': close_index
                }
            )

            print(data_map)

        def get_nasdaq():
            time_list = []

            response = requests.get(url_nasdaq, timeout=10)
            resp_json = response.json()
            begin_timestamp = int(str(resp_json['chart_begin_time'])[:-3])
            begin_time = datetime.datetime.utcfromtimestamp(begin_timestamp) + datetime.timedelta(hours=13)
            begin_time = begin_time.strftime('%Y-%m-%d')

            open_index = resp_json['Open']

            data = resp_json['data']

            data_list = []
            for dt in data:
                index_timestamp = int(str(dt['x'])[:-3])
                index_time = datetime.datetime.utcfromtimestamp(index_timestamp) + datetime.timedelta(hours=13)
                if index_time.strftime('%S') == '59':
                    index_time = index_time + datetime.timedelta(minutes=1)
                index_time = index_time.strftime('%Y-%m-%d %H:%M') + ':00'
                index_time = datetime.datetime.strptime(index_time, '%Y-%m-%d %H:%M:%S')

                if index_time not in time_list:
                    time_list.append(index_time)

                index_value = dt['y']
                data_list.append([index_time, index_value])

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == '05:00:00':
                close_index = data_list[-1][1]
                if close_index != float(resp_json['Value']):
                    close_index = float(resp_json['Value'])

            data_map = {}
            data_map.update({'name': 'nasdaq'})
            data_map.update(
                {
                    'begin_time': begin_time,
                    'open_index': open_index,
                    'data_list': data_list,
                    'close_index': close_index
                }
            )
            # print(data_map)

            return time_list

        def get_djia():
            time_list = []
            response = requests.get(url_djia, timeout=10)
            resp_json = response.json()
            begin_timestamp = int(str(resp_json['chart_begin_time'])[:-3])
            begin_time = datetime.datetime.utcfromtimestamp(begin_timestamp) + datetime.timedelta(hours=13)
            begin_time = begin_time.strftime('%Y-%m-%d')

            open_index = resp_json['Open']

            data = resp_json['data']

            data_list = []
            for dt in data:
                index_timestamp = int(str(dt['x'])[:-3])
                index_time = datetime.datetime.utcfromtimestamp(index_timestamp) + datetime.timedelta(hours=13)
                if index_time.strftime('%S') == '59' or index_time.strftime('%S') == '58':
                    index_time = index_time + datetime.timedelta(minutes=1)
                index_time = index_time.strftime('%Y-%m-%d %H:%M') + ':00'
                index_time = datetime.datetime.strptime(index_time, '%Y-%m-%d %H:%M:%S')

                if index_time not in time_list:
                    time_list.append(index_time)

                index_value = dt['y']
                data_list.append([index_time, index_value])

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == '05:00:00':
                close_index = data_list[-1][1]
                if close_index != float(resp_json['Value']):
                    close_index = float(resp_json['Value'])

            data_map = {}
            data_map.update({'name': 'djia'})
            data_map.update(
                {
                    'begin_time': begin_time,
                    'open_index': open_index,
                    'data_list': data_list,
                    'close_index': close_index
                }
            )

            # print(data_map)

            return time_list

        def get_hsi():
            response = requests.get(url_hsi, headers=headers, timeout=10)
            resp_display = response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']

            begin_time = resp_display['update']['text'].replace('/', '-').split(' ')[0]
            data = resp_display['tab']['p'].split(';')[:-1]

            data_list = []
            for dt in data:
                info_list = dt.split(',')
                index_time = datetime.datetime.strptime(begin_time + ' ' + info_list[0] + ':00', "%Y-%m-%d %H:%M:%S")
                index_value = float(info_list[1])
                data_list.append([index_time, index_value])

            open_index = data_list[0][1]

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == '16:00:00':
                close_index = data_list[-1][1]
                if close_index != float(resp_display['cur']['num']):
                    close_index = float(resp_display['cur']['num'])

            data_map = {}
            data_map.update({'name': 'hsi'})
            data_map.update(
                {
                    'begin_time': begin_time,
                    'open_index': open_index,
                    'data_list': data_list,
                    'close_index': close_index
                }
            )

            print(data_map)

        # from time import sleep
        # for i in range(0, 100):
        #     print('========================', i)
        #     get_djia()
        #     print('========================', i)
        #     sleep(61)
        # djia_time_list = get_hsi()
        # nasdaq_time_list = get_hsi()
        #
        # print('nasdaq len ========= ', len(nasdaq_time_list))
        # print('djia len ========= ', len(djia_time_list))
        #
        # print(set(djia_time_list) - set(nasdaq_time_list))
        #
        # print(datetime.datetime.utcfromtimestamp(1541583782))
        # print(datetime.datetime.utcfromtimestamp(1541583839))

        print('flag ', datetime.datetime.now())
        print('=================================================')
