# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from django.core.management import call_command


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

        # url_dji = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d&eprop=minute'
        # url_ndx = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=纳斯达克&hilight=disp_data.*.title&sitesign=12299ccd2e71da74cd27339159e1a3ba&eprop=minute'
        # response = requests.get(url_dji, headers=headers)
        # data_list = response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['tab']['p'].split(';')[
        #             :-1]
        # date_ymd = data_list[0].split(',')[2].split(' ')[0].replace('/', '-')
        # print(data_list[0].split(','))

        # if len(re.findall('.*\((.*?:.*?)\)', result_score)) > 0:
        #     host_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][1]
        #     guest_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][0]
        #     print(host_team_score)
        #
        #     result_list = soup.select('table[class="kj-table"]')
        #     result_mnl = result_list[0].select('span[class="win"]')[0].string.replace(' ', '')
        #     print(result_mnl)
        #
        #     result_hdc = result_list[1].select('span[class="win"]')[0].string
        #     result_hdc_flag = result_match['result_hdc'][result_hdc]
        #     print(result_hdc_flag)
        #
        #     result_hilo = result_list[2].select('span[class="win"]')[0].string
        #     result_hilo_flag = result_match['result_hilo'][result_hilo]
        #     print(result_hilo_flag)
        #
        #     result_wnm = result_list[3].select('span[class="win"]')[0].string
        #     result_wnm_flag = result_match['result_wnm'][result_wnm]
        #     print(result_wnm_flag)
        #
        # else:
        #     print(match_flag + ',' + '未有开奖信息')

        from quiz.models import Record
        from promotion.models import PromotionRecord
        from django.db.models import Q
        promotion_list = []
        for record in Record.objects.filter(~Q(source=str(Record.CONSOLE)), quiz_id=3986):
            # 构建promotion_dic
            if record.source != str(Record.CONSOLE) and record.roomquiz_id != 1:
                promotion_list.append({'record_id': record.id, 'source': 1, 'earn_coin': record.earn_coin, 'status': 1})
        # 推广代理事宜
        PromotionRecord.objects.insert_all(promotion_list)
















