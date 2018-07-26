# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Index, Periods
from .stock_result import ergodic_record, newobject
import requests
import datetime
from utils.cache import *
import time

url_HSI = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=aff194940ee6db5fcb462df18a36f9fd'
url_DJA = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d'
url_DJA_other = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery17202690225701728284_1532446114928&type=CT&cmd=DJIA_UI&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'
url_SHANG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E4%B8%8A%E8%AF%81%E6%8C%87%E6%95%B0&hilight=disp_data.*.title'
url_SHENG = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8190&from_mid=1&query=%E6%B7%B1%E8%AF%81%E6%88%90%E6%8C%87&hilight=disp_data.*.title'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
market_rest_cn_list = ['2018-06-18', '2018-09-24', '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04', '2018-10-05']
market_rest_en_dic = ['2018-09-03', '2018-11-22', '2018-12-25']
market_rese_hk_dic = ['2018-09-25', '2018-10-01', '2018-10-17', '2018-12-25', '2018-12-26']
market_rest_cn_end_time = ['11:30:00', '15:00:00']
market_hk_end_time = ['12:00:00', '16:10:00']
market_en_end_time = ['4:00:00']

market_rest_cn_start_time = ['09:30:00', '13:00:00']
market_hk_start_time = ['09:30:00', '13:00:00']
market_en_start_time = ['21:30:00']

market_rest_cn_end_time = ['11:30:00', '15:00:00']
market_hk_end_time = ['12:00:00', '16:10:00']
market_en_end_time = ['04:00:00']


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
    response = requests.get(base_url, headers=headers)
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


def get_dja(period, url, dt):
    if dt['type'] == str(1):
        response = requests.get(url, headers=headers)
        if period.start_value is None:
            period.start_value = response.text.split(',')[-5]
            period.save()
        if response.text.split(',')[-1][:-2] == get_cache(period.stock.STOCK[int(period.stock.name)][1]):
            print('时间相同不存储')
            # pass
        else:
            print('时间不同开始存储')
            set_cache(period.stock.STOCK[int(period.stock.name)][1], response.text.split(',')[-1][:-2])
            index = Index()
            index.periods = period
            index.index_value = float(response.text.split(',')[3])
            index.save()

    elif dt['type'] == str(2):
        date_hour = dt['date'].split(' ')[0] + ' ' + dt['date'].split(' ')[1].split(':')[0]
        # print(date_hour)
        # print(period.lottery_time.strftime('%Y-%m-%d %H'))
        if date_hour == period.lottery_time.strftime('%Y-%m-%d %H'):
            ergodic_record(period, dt)
            return True


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
            return True


def confirm_time(period):
    date_now = time.mktime(datetime.datetime.now().timetuple())
    lottery_time = period.lottery_time.strftime('%Y-%m-%d %H:%M:%S')
    if period.stock.name == '0' or period.stock.name == '1':
        i = market_rest_cn_end_time.index(lottery_time.split(' ')[1])
        date_start = lottery_time.split(' ')[0] + ' ' + market_rest_cn_start_time[i]
        date_end = lottery_time.split(' ')[0] + ' ' + market_rest_cn_end_time[i]
    elif period.stock.name == '2':
        i = market_hk_end_time.index(lottery_time.split(' ')[1])
        date_start = lottery_time.split(' ')[0] + ' ' + market_hk_start_time[i]
        date_end = lottery_time.split(' ')[0] + ' ' + market_hk_end_time[i]
    elif period.stock.name == '3':
        i = market_en_end_time.index(lottery_time.split(' ')[1])
        date_start = lottery_time.split(' ')[0] + ' ' + market_en_start_time[i]
        date_end = lottery_time.split(' ')[0] + ' ' + market_en_end_time[i]

    start = datetime.datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(minutes=15)
    end = datetime.datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=30)
    if period.stock.name == '3':
        start = start - datetime.timedelta(days=1)

    start = time.mktime(start.timetuple())
    end = time.mktime(end.timetuple())

    if start <= date_now <= end:
        return True


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        for i in range(9999999):
            time.sleep(20)
            if Periods.objects.filter(is_result=False).exists() is not True:
                print('暂无行情')
            else:
                """
                上证指数，深证成指
                """
                print('上证指数：')
                if Periods.objects.filter(is_result=False, stock__name='0').exists():
                    period = Periods.objects.filter(is_result=False, stock__name='0').first()
                    if confirm_time(period) is not True:
                        print('空闲时间, 空闲时间')
                    else:
                        dt_shang = get_index(url_SHANG)
                        print(dt_shang)
                        flag = open_prize(period, dt_shang)

                        if flag is True:
                            # 开奖后放出题目
                            print('放出题目')
                            open_date = dt_shang['date'].split(' ')[0]
                            now_date = datetime.datetime.now().date()
                            count = Periods.objects.filter(stock__name='0', lottery_time__date=now_date).count()
                            if count == 1:
                                next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[1],
                                                                  '%Y-%m-%d %H:%M:%S')
                            else:
                                next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                while next.isoweekday(self) >= 6 or next in market_rest_cn_list:
                                    next += datetime.timedelta(1)
                            per = int(period.periods) + 1
                            newobject(str(per), period.stock_id, next)

                print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')

                print('深证成指：')
                if Periods.objects.filter(is_result=False, stock__name='1').exists():
                    period = Periods.objects.filter(is_result=False, stock__name='1').first()
                    if confirm_time(period) is not True:
                        print('空闲时间, 空闲时间')
                    else:
                        dt_sheng = get_index(url_SHENG)
                        print(dt_sheng)
                        flag = open_prize(period, dt_sheng)

                        if flag is True:
                            # 开奖后放出题目
                            print('放出题目')
                            open_date = dt_sheng['date'].split(' ')[0]
                            now_date = datetime.datetime.now().date()
                            count = Periods.objects.filter(stock__name='1', lottery_time__date=now_date).count()
                            if count == 1:
                                next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[1],
                                                                  '%Y-%m-%d %H:%M:%S')
                            else:
                                next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                while next.isoweekday(self) >= 6 or next in market_rest_cn_list:
                                    next += datetime.timedelta(1)
                            per = int(period.periods) + 1
                            newobject(str(per), period.stock_id, next)
                print('------------------------------------------------------------------------------------')

                """
                恒生指数
                """
                print('恒生指数：')
                if Periods.objects.filter(is_result=False, stock__name='2').exists():
                    period = Periods.objects.filter(is_result=False, stock__name='2').first()
                    if confirm_time(period) is not True:
                        print('空闲时间, 空闲时间')
                    else:
                        dt_hsi = get_index(url_HSI)
                        print(dt_hsi)
                        flag = open_prize(period, dt_hsi)
                        if flag is True:
                            # 开奖后放出题目
                            print('放出题目')
                            open_date = dt_hsi['date'].split(' ')[0]
                            now_date = datetime.datetime.now().date()
                            count = Periods.objects.filter(stock__name='2', lottery_time__date=now_date).count()
                            if count == 1:
                                next = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[1], '%Y-%m-%d %H:%M:%S')
                                if open_date in ['2018-12-24', '2018-12-31']:
                                    next = datetime.datetime.strptime(open_date + ' ' +market_hk_end_time[0],'%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                    while next.isoweekday(self) >= 6 or next in market_rese_hk_dic:
                                        next += datetime.timedelta(1)
                            else:
                                next = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                while next.isoweekday(self) >= 6 or next in market_rese_hk_dic:
                                    next += datetime.timedelta(1)
                            per = int(period.periods) + 1
                            newobject(str(per), period.stock_id, next)
                print('------------------------------------------------------------------------------------')

                """
                道琼斯指数
                """
                print('道琼斯：')
                if Periods.objects.filter(is_result=False, stock__name='3').exists():
                    period = Periods.objects.filter(is_result=False, stock__name='3').first()
                    if confirm_time(period) is not True:
                        print('空闲时间, 空闲时间')
                    else:
                        dt_dja = get_index(url_DJA)
                        print(dt_dja)
                        flag = get_dja(period, url_DJA_other, dt_dja)
                        if flag is  True:
                            # 开奖后放出题目
                            print('放出题目')
                            open_date = dt_dja['date'].split(' ')[0]
                            now_date = datetime.datetime.now().date()
                            count = Periods.objects.filter(stock__name='3', lottery_time__date=now_date).count()
                            if count == 0:
                                next = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0], '%Y-%m-%d %H:%M:%S')
                            else:
                                next = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0],
                                                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                while next.isoweekday(self) >= 6 or next in market_en_end_time:
                                    next += datetime.timedelta(1)
                            per = int(period.periods) + 1
                            newobject(str(per), period.stock_id, next)
                print('------------------------------------------------------------------------------------')

