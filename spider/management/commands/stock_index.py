# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import datetime

url_HSI = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=aff194940ee6db5fcb462df18a36f9fd'
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
    tomorrow_cn = datetime.datetime.now() + datetime.timedelta(days=1)
    tomorrow_en = datetime.datetime.now() - datetime.timedelta(hours=12) + datetime.timedelta(days=1)
    if tomorrow_en.isoweekday() >= 6:
        return False
    return True


def get_index(base_url):
    response = requests.get(base_url)
    print(response.json()['data'][0]['disp_data'][0]['status'])
    print(response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['cur'])
    print(response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['update'])
    print(response.json()['data'][0]['disp_data'][0]['code'])


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        """
        上证指数，深证成指
        """
        # 开奖
        print('上证指数：')
        get_index(url_SHANG)
        print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')

        print('深证成指：')
        get_index(url_SHENG)

        # 开奖后放出题目，先判断明天是否休市
        if market_rest_cn():
            print('放出题目')
        else:
            print('中国股市明天休市')
        print('------------------------------------------------------------------------------------')

        """
        道琼斯指数
        """
        # 开奖
        print('道琼斯指数：')
        get_index(url_DJA)

        # 开奖后放出题目，先判断明天是否休市
        if market_rest_en():
            print('放出题目')
        else:
            print('美国股市明天休市')
        print('------------------------------------------------------------------------------------')

        """
        恒生指数
        """
        # 开奖
        print('恒生指数：')
        get_index(url_HSI)

        # 开奖后放出题目，先判断明天是否休市
        if market_rest_cn():
            print('放出题目')
        else:
            print('中国股市明天休市')
        print('------------------------------------------------------------------------------------')


