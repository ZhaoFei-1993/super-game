# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Index, Periods
from .stock_result import ergodic_record
import requests
import datetime
from utils.cache import *
from time import sleep

url_HSI = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=aff194940ee6db5fcb462df18a36f9fd'
# url_DJA = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=4a952b2e6c8f78cb7956a505727f39c0'
url_DJA = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d'
url_SHANG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E4%B8%8A%E8%AF%81%E6%8C%87%E6%95%B0&hilight=disp_data.*.title'
url_SHENG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E6%B7%B1%E8%AF%81%E6%88%90%E6%8C%87&hilight=disp_data.*.title'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
market_rest_cn_list = ['2018-06-18', '2018-09-24', '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04', '2018-10-05']
market_rest_en_dic = ['2018-09-03', '2018-11-22', '2018-12-25']


def market_rest_cn():
    tomorrow_cn = datetime.datetime.now() + datetime.timedelta(days=1)
    if tomorrow_cn.strftime('%Y-%m-%d') in market_rest_cn_list:
        return False
    if tomorrow_cn.isoweekday() >= 6:
        return False
    return True


def market_rest_en():
    tomorrow_en = datetime.datetime.now() - datetime.timedelta(hours=12) + datetime.timedelta(days=1)
    if tomorrow_en.strftime('%Y-%m-%d') in market_rest_cn_list:
        return False
    if tomorrow_en.isoweekday() >= 6:
        return False
    return True


def get_index(base_url):
    response = requests.get(base_url)
    # print(response.json()['data'][0]['disp_data'][0]['status'])
    # print(response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['cur'])
    # print(response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['update'])
    # print(response.json()['data'][0]['disp_data'][0]['code'])
    dt_dic = {
        'num': response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['cur']['num'],
        'start_value': response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['info'][0]['value'],
        'status': response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['cur']['status'],
        'date': response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['update']['text'].replace(
            '/', '-'),
        'type': response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['update']['type'],
    }
    return dt_dic


def open_prize(period, dt):
    if dt['type'] == str(1):
        if period.start_value is None:
            period.start_value = float(dt['start_value'])
            period.save()
        if dt['date'] == get_cache(period.stock.STOCK[int(period.stock.name)][1]):
            print('时间相同不存储')
            # pass
        else:
            print('时间不同开始存储')
            set_cache(period.stock.STOCK[int(period.stock.name)][1], dt['date'])
            index = Index()
            index.periods = period
            index.index_value = float(dt['num'])
            index.save()

    elif dt['type'] == str(2):
        date_hour = dt['date'].split(' ')[0] + ' ' + dt['date'].split(' ')[1].split(':')[0]
        # print(date_hour)
        # print(period.lottery_time.strftime('%Y-%m-%d %H'))
        if date_hour == period.lottery_time.strftime('%Y-%m-%d %H'):
            ergodic_record(period, dt)


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        for i in range(999999999999):
            sleep(25)
            """
            上证指数，深证成指
            """
            print('上证指数：')
            dt_shang = get_index(url_SHANG)
            print(dt_shang)
            if Periods.objects.filter(is_result=False, stock__name='0').exists():
                period = Periods.objects.filter(is_result=False, stock__name='0').first()
                open_prize(period, dt_shang)

            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')

            print('深证成指：')
            dt_sheng = get_index(url_SHENG)
            print(dt_sheng)
            if Periods.objects.filter(is_result=False, stock__name='1').exists():
                period = Periods.objects.filter(is_result=False, stock__name='1').first()
                open_prize(period, dt_sheng)

            # 开奖后放出题目，先判断明天是否休市
            if market_rest_cn():
                print('放出题目')
            else:
                print('中国股市明天休市')
            print('------------------------------------------------------------------------------------')

            """
            道琼斯指数
            """
            print('道琼斯：')
            dt_dja = get_index(url_DJA)
            print(dt_dja)
            if Periods.objects.filter(is_result=False, stock__name='3').exists():
                period = Periods.objects.filter(is_result=False, stock__name='3').first()
                open_prize(period, dt_dja)

            # 开奖后放出题目，先判断明天是否休市
            if market_rest_en():
                print('放出题目')
            else:
                print('美国股市明天休市')
            print('------------------------------------------------------------------------------------')

            """
            恒生指数
            """
            print('恒生指数：')
            dt_hsi = get_index(url_HSI)
            print(dt_hsi)
            if Periods.objects.filter(is_result=False, stock__name='2').exists():
                period = Periods.objects.filter(is_result=False, stock__name='2').first()
                open_prize(period, dt_hsi)

            # 开奖后放出题目，先判断明天是否休市
            if market_rest_cn():
                print('放出题目')
            else:
                print('中国股市明天休市')
            print('------------------------------------------------------------------------------------')
