# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Index, Periods, Index_day
from .stock_result import ergodic_record, newobject
import requests
import datetime
from utils.cache import *
import time
import re
import local_settings

url_HSI = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery172010717678041953493_1532447528063&type=CT&cmd=HSI5&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'
url_DJA = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery17202690225701728284_1532446114928&type=CT&cmd=DJIA_UI&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'
url_SHANG = 'http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?rtntype=5&token=4f1862fc3b5e77c150a2b985b12db0fd&cb=jQuery18302986275421321969_1532447305292&id=0000011'
url_SHENG = 'http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?rtntype=5&token=4f1862fc3b5e77c150a2b985b12db0fd&cb=jQuery18306190742815473158_1532447588005&id=3990012'

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


def get_index_cn(period, base_url):
    date_now = datetime.datetime.now()
    date_ymd = datetime.datetime.now().strftime('%Y-%m-%d')
    date_day = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                          "%Y-%m-%d %H:%M:%S")
    stock_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd
    response = requests.get(base_url, headers=headers)
    dt_dic = eval(re.findall('\(.*?\)', response.text)[0][1:-1])
    data_list = dt_dic['data']
    if period.start_value is None:
        period.start_value = float(dt_dic['info']['o'])
        period.save()
    if date_now < period.lottery_time:
        if data_list[0].split(' ') == date_ymd:
            if get_cache(stock_cache_name) is None:
                for data in data_list:
                    dt = data.split(',')
                    index = Index()
                    index.periods = period
                    index.index_value = float(dt[1])
                    index.save()
                    index.index_time = datetime.datetime.strptime(dt[0] + ':00', "%Y-%m-%d %H:%M:%S")
                    index.save()
                index_day = Index_day()
                index_day.stock_id = period.stock.id
                index_day.index_value = float(data_list[-1].split(',')[1])
                index_day.save()
                index_day.created_at = date_day
                index_day.save()
                set_cache(stock_cache_name, '@'.join(data_list), 86400)
            else:
                result_list = get_cache(stock_cache_name).split('@')
                if data_list != result_list:
                    for data in data_list:
                        if data not in result_list:
                            dt = data.split(',')
                            index = Index()
                            index.periods = period
                            index.index_value = float(dt[1])
                            index.save()
                            index.index_time = datetime.datetime.strptime(dt[0] + ':00', "%Y-%m-%d %H:%M:%S")
                            index.save()

                            if data_list.index(data) == len(data_list) - 1:
                                index_day = Index_day.objects.filter(stock_id=period.stock.id,
                                                                     created_at=date_day).first()
                                index_day.index_value = float(dt['num'])
                                index_day.save()
                    set_cache(stock_cache_name, '@'.join(data_list), 86400)
    else:
        num_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd + '_num'
        num = data_list[-1].split(',')[1]
        time = data_list[-1].split(',')[0]
        if get_cache(num_cache_name) is None:
            set_cache(num_cache_name, num + ',' + time + ',1', 3600)
        else:
            cache_dt = get_cache(num_cache_name)
            print(cache_dt)
            if cache_dt.split(',')[0] == num:
                count = int(cache_dt.split(',')[2]) + 1
                if count >= 6:
                    if float(period.start_value) > float(num):
                        status = 'up'
                    elif float(period.start_value) == float(num):
                        status = 'draw'
                    elif float(period.start_value) < float(num):
                        status = 'down'

                    param_dic = {
                        'num': num, 'status': status, 'auto': local_settings.GUESS_RESULT_AUTO,
                    }
                    ergodic_record(period, param_dic, date_day)
                    return True
                else:
                    set_cache(num_cache_name, num + ',' + time + ',' + str(count), 3600)
            else:
                set_cache(num_cache_name, num + ',' + time + ',1', 3600)


def get_index_hk_en(period, base_url):
    date_ymd = datetime.datetime.now().strftime('%Y-%m-%d')
    date_day = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                          "%Y-%m-%d %H:%M:%S")
    stock_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd
    response = requests.get(base_url, headers=headers)
    dt_list = re.findall('\(.*?\)', response.text)[0][1:-1].split(',')
    param_dic = {
        'num': dt_list[3], 'start_value': dt_list[6], 'date': dt_list[-1][:-1], 'type': dt_list[-2],
    }
    if period.start_value is None:
        period.start_value = float(param_dic['start_value'])
        period.save()
    if int(param_dic['type']) == 0:
        if dt_list[-1] == get_cache(stock_cache_name):
            print('时间相同不存储')
        else:
            print('时间不同开始存储')
            set_cache(stock_cache_name, param_dic['date'], 86400)
            index = Index()
            index.periods = period
            index.index_value = float(param_dic['num'])
            index.save()

            if Index_day.objects.filter(stock_id=period.stock.id, created_at=date_day).exists():
                index_day = Index_day.objects.filter(stock_id=period.stock.id, created_at=date_day).first()
                index_day.index_value = float(param_dic['num'])
                index_day.save()
            else:
                index_day = Index_day()
                index_day.stock_id = period.stock.id
                index_day.index_value = float(param_dic['num'])
                index_day.save()
                index_day.created_at = date_day
                index_day.save()
    elif int(param_dic['type']) == 1:
        num_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd + '_num'
        num = param_dic['num']
        time = param_dic['date']
        if get_cache(num_cache_name) is None:
            set_cache(num_cache_name, num + ',' + time + ',1', 3600)
        else:
            cache_dt = get_cache(num_cache_name)
            print(cache_dt)
            if cache_dt.split(',')[0] == num:
                count = int(cache_dt.split(',')[2]) + 1
                if count >= 6:
                    if float(period.start_value) > float(num):
                        status = 'up'
                    elif float(period.start_value) == float(num):
                        status = 'draw'
                    elif float(period.start_value) < float(num):
                        status = 'down'

                    param_dic = {
                        'num': num, 'status': status, 'auto': local_settings.GUESS_RESULT_AUTO,
                    }
                    ergodic_record(period, param_dic, date_day)
                    return True
                else:
                    set_cache(num_cache_name, num + ',' + time + ',' + str(count), 3600)
            else:
                set_cache(num_cache_name, num + ',' + time + ',1', 3600)


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
    end = datetime.datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S")
    if period.stock.name == '3':
        start = start - datetime.timedelta(days=1)

    start = time.mktime(start.timetuple())
    end = time.mktime(end.timetuple())

    if start <= date_now <= end:
        return True


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        if Periods.objects.filter(is_result=False).exists() is not True:
            print('暂无行情')
        else:
            """
            上证指数，深证成指
            """
            print('上证指数：')
            if Periods.objects.filter(is_result=False, stock__name='0').exists():
                period = Periods.objects.filter(is_result=False, stock__name='0').first()
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='0',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_shang = get_index_cn(period, url_SHANG)
                    # print(dt_shang)
                    flag = get_index_cn(period, url_SHANG)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        now_date = datetime.datetime.now().date()
                        count = Periods.objects.filter(stock__name='0', lottery_time__date=now_date).count()
                        if count == 1:
                            next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[1],
                                                              '%Y-%m-%d %H:%M:%S')
                        else:
                            next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                            while next.isoweekday() >= 6 or next.strftime('%Y-%m-%d') in market_rest_cn_list:
                                next += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        newobject(str(per), period.stock_id, next)

            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')

            print('深证成指：')
            if Periods.objects.filter(is_result=False, stock__name='1').exists():
                period = Periods.objects.filter(is_result=False, stock__name='1').first()
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='1',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_sheng = get_index_cn(period, url_SHENG)
                    # print(dt_sheng)
                    flag = get_index_cn(period, url_SHENG)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        now_date = datetime.datetime.now().date()
                        count = Periods.objects.filter(stock__name='1', lottery_time__date=now_date).count()
                        if count == 1:
                            next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[1],
                                                              '%Y-%m-%d %H:%M:%S')
                        else:
                            next = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                            while next.isoweekday() >= 6 or next.strftime('%Y-%m-%d') in market_rest_cn_list:
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
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='2',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_hsi = get_index_hk_en(period, url_HSI)
                    # print(dt_hsi)
                    flag = get_index_hk_en(period, url_HSI)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        now_date = datetime.datetime.now().date()
                        count = Periods.objects.filter(stock__name='2', lottery_time__date=now_date).count()
                        if count == 1:
                            next = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[1],
                                                              '%Y-%m-%d %H:%M:%S')
                            if open_date in ['2018-12-24', '2018-12-31']:
                                next = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                                                  '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                                while next.isoweekday() >= 6 or next in market_rese_hk_dic:
                                    next += datetime.timedelta(1)
                        else:
                            next = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                            while next.isoweekday() >= 6 or next.strftime('%Y-%m-%d') in market_rest_cn_list:
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
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='3',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_dja = get_index_hk_en(period, url_DJA)
                    # print(dt_dja)
                    flag = get_index_hk_en(period, url_DJA)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        now_date = datetime.datetime.now().date()
                        count = Periods.objects.filter(stock__name='3', lottery_time__date=now_date).count()
                        if count == 0:
                            next = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S')
                        else:
                            next = datetime.datetime.strptime(open_date + ' ' + market_en_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                            while (next-datetime.timedelta(hours=12)).isoweekday() >= 6 or (next-datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in market_en_end_time:
                                next += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        newobject(str(per), period.stock_id, next)
            print('------------------------------------------------------------------------------------')

