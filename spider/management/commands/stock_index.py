# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Index, Periods, Index_day, Issues, Stock
from .stock_result_new import GuessRecording, GuessPKRecording
import requests
import datetime
from utils.cache import *
import re
import local_settings
from guess.consumers import guess_graph

url_HSI = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery172010717678041953493_1532447528063&type=CT&cmd=HSI5&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'
url_DJA = 'http://nufm.dfcfw.com/EM_Finance2014NumericApplication/JS.aspx?cb=jQuery17202690225701728284_1532446114928&type=CT&cmd=DJIA_UI&sty=OCGIFO&st=z&js=((x))&token=4f1862fc3b5e77c150a2b985b12db0fd'
url_SHANG = 'http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?rtntype=5&token=4f1862fc3b5e77c150a2b985b12db0fd&cb=jQuery18302986275421321969_1532447305292&id=0000011'
url_SHENG = 'http://pdfm.eastmoney.com/EM_UBG_PDTI_Fast/api/js?rtntype=5&token=4f1862fc3b5e77c150a2b985b12db0fd&cb=jQuery18306190742815473158_1532447588005&id=3990012'

url_dji = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=%E9%81%93%E7%90%BC%E6%96%AF&hilight=disp_data.*.title&sitesign=57f039002f70ed02eec684164dad4e7d&eprop=minute'
url_ndx = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8191&from_mid=1&query=纳斯达克&hilight=disp_data.*.title&sitesign=12299ccd2e71da74cd27339159e1a3ba&eprop=minute'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Connection': 'close',
}

market_rest_cn_list = ['2018-06-18', '2018-09-24', '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04', '2018-10-05']
market_rest_en_dic = ['2018-09-03', '2018-11-22', '2018-12-25']
market_rest_hk_dic = ['2018-09-25', '2018-10-01', '2018-10-17', '2018-12-25', '2018-12-26']

market_rest_cn_start_time = ['09:30:00']
market_hk_start_time = ['09:30:00']
market_en_start_time = ['21:30:00']
market_en_start_time_winter = ['22:30:00']

market_rest_cn_end_time = ['15:00:00']
market_hk_end_time = ['16:10:00']
market_en_end_time = ['04:00:00']
market_en_end_time_winter = ['05:00:00']


def get_index_cn(period, base_url):
    guess_recording = GuessRecording()
    date_now = datetime.datetime.now()
    new_index_dic = {'x': [], 'y': []}
    date_ymd = datetime.datetime.now().strftime('%Y-%m-%d')
    date_day = datetime.datetime.strptime(period.lottery_time.strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                          "%Y-%m-%d %H:%M:%S")
    stock_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd
    response = requests.get(base_url, headers=headers)
    content_text = response.text.replace('false', 'False')
    dt_dic = eval(re.findall('\(.*?\)', content_text)[0][1:-1])
    data_list = dt_dic['data']
    if period.start_value is None or float(period.start_value) != float(dt_dic['info']['o']):
        period.start_value = float(dt_dic['info']['o'])
        period.save()
    if date_now < period.lottery_time or \
            Index.objects.filter(periods_id=period.id, index_time=period.lottery_time).exists() is not True:
        if data_list[0].split(' ')[0] == date_ymd:
            if get_cache(stock_cache_name) is None:
                for data in data_list:
                    dt = data.split(',')
                    value = float(dt[1])
                    index_time = datetime.datetime.strptime(dt[0] + ':00', "%Y-%m-%d %H:%M:%S")

                    print('第一次次开始存储 ')
                    print('value===> ', value)
                    print('time====>', index_time)

                    index = Index()
                    index.periods = period
                    index.index_value = value
                    index.save()
                    index.index_time = index_time
                    index.save()

                    new_index_dic['x'].append(index_time.strftime("%H:%M"))
                    new_index_dic['y'].append(str(value))

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
                        dt = data.split(',')
                        value = float(dt[1])
                        index_time = datetime.datetime.strptime(dt[0] + ':00', "%Y-%m-%d %H:%M:%S")

                        flag = False
                        if data not in result_list:
                            for i in result_list:
                                result_dt = i.split(',')
                                result_index_time = datetime.datetime.strptime(result_dt[0] + ':00',
                                                                               "%Y-%m-%d %H:%M:%S")
                                # print(index_time)
                                # print(result_index_time)
                                if index_time == result_index_time:
                                    print('再次开始存储,已存储时间但数值变动')
                                    print('value===> ', value)
                                    print('time====>', index_time)

                                    index = Index.objects.filter(periods=period, index_time=result_index_time).first()
                                    index.index_value = value
                                    index.save()
                                    flag = True
                                    break

                            if flag is True:
                                pass
                            else:
                                print('再次开始存储,新时间')
                                print('value===> ', value)
                                print('time====>', index_time)

                                index = Index()
                                index.periods = period
                                index.index_value = value
                                index.save()
                                index.index_time = index_time
                                index.save()

                                new_index_dic['x'].append(index_time.strftime("%H:%M"))
                                new_index_dic['y'].append(str(value))

                            if data_list.index(data) == len(data_list) - 1:
                                index_day = Index_day.objects.filter(stock_id=period.stock.id,
                                                                     created_at=date_day).first()
                                index_day.index_value = float(dt[1])
                                index_day.save()
                    set_cache(stock_cache_name, '@'.join(data_list), 86400)
            # 推送曲线图数据
            if len(new_index_dic['x']) > 0:
                guess_graph(period.id, new_index_dic)
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
                    # 最后一期的确认
                    index_time = datetime.datetime.strptime(time + ':00', "%Y-%m-%d %H:%M:%S")
                    index = Index.objects.filter(periods=period, index_time=index_time).first()
                    index.index_value = num
                    index.save()

                    if float(period.start_value) > float(num):
                        status = 'down'
                    elif float(period.start_value) == float(num):
                        status = 'draw'
                    elif float(period.start_value) < float(num):
                        status = 'up'

                    param_dic = {
                        'num': num, 'status': status, 'auto': local_settings.GUESS_RESULT_AUTO,
                    }
                    guess_recording.take_result(period, param_dic, date_day)
                    return True
                else:
                    set_cache(num_cache_name, num + ',' + time + ',' + str(count), 3600)
            else:
                set_cache(num_cache_name, num + ',' + time + ',1', 3600)


def get_index_hk_en(period, base_url):
    guess_recording = GuessRecording()
    date_now = datetime.datetime.now()
    date_ymd = datetime.datetime.now().strftime('%Y-%m-%d')
    date_day = datetime.datetime.strptime(period.lottery_time.strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                          "%Y-%m-%d %H:%M:%S")
    stock_cache_name = period.stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd
    response = requests.get(base_url, headers=headers)
    dt_list = re.findall('\(.*?\)', response.text)[0][1:-1].split(',')
    param_dic = {
        'num': dt_list[3], 'start_value': dt_list[6], 'date': dt_list[-1][:-1], 'type': dt_list[-2],
    }
    if period.start_value is None or float(period.start_value) != float(param_dic['start_value']):
        period.start_value = float(param_dic['start_value'])
        period.save()
    if int(param_dic['type']) == 0:
        rest_start = datetime.datetime.strptime(date_ymd + ' ' + '12:00:00', "%Y-%m-%d %H:%M:%S")
        rest_end = datetime.datetime.strptime(date_ymd + ' ' + '13:00:00', "%Y-%m-%d %H:%M:%S")
        if dt_list[-1] == get_cache(stock_cache_name) or (rest_start <= date_now <= rest_end):
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
    elif (int(param_dic['type']) == 1 or int(param_dic['type']) == 2) and (date_now > period.lottery_time):
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
                    guess_recording.take_result(period, param_dic, date_day)
                    return True
                else:
                    set_cache(num_cache_name, num + ',' + time + ',' + str(count), 3600)
            else:
                set_cache(num_cache_name, num + ',' + time + ',1', 3600)


def get_index_en(period, base_url):
    guess_recording = GuessRecording()
    response = requests.get(base_url, headers=headers)
    data_list = response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['tab']['p'].split(';')[:-1]
    date_ymd = response.json()['data'][0]['disp_data'][0]['property'][0]['data']['display']['update']['text'].replace(
        '/', '-').split(' ')[0]
    index_info = []
    if date_ymd == (period.lottery_time - datetime.timedelta(hours=12)).strftime('%Y-%m-%d'):
        for i in data_list:
            info_list = i.split(',')
            index_time = datetime.datetime.strptime(date_ymd + ' ' + info_list[0] + ':00',
                                                    "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=13)
            index_time_str = index_time.strftime("%Y-%m-%d %H:%M:%S")
            index_info.append({
                'index_time': index_time,
                'index_time_str': index_time_str,
                'index_value': info_list[1],
            })
    if len(data_list) == 0:
        print('未有数据')
        return

    cache_name = Stock.STOCK[int(period.stock.name)][0] + '_' + 'period_' + str(period.id)

    date_now = datetime.datetime.now()
    date_day = datetime.datetime.strptime(period.lottery_time.strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                          "%Y-%m-%d %H:%M:%S")
    new_index_dic = {'x': [], 'y': []}
    if period.start_value is None or float(period.start_value) != float(index_info[0]['index_value']):
        period.start_value = float(index_info[0]['index_value'])
        period.save()
    if date_now < period.lottery_time or \
            Index.objects.filter(periods_id=period.id, index_time=period.lottery_time).exists() is not True:
        if get_cache(cache_name) is None:
            for data in index_info:
                value = float(data['index_value'])
                index_time = data['index_time']

                print('第一次次开始存储 ')
                print('value===> ', value)
                print('time====>', index_time)

                index = Index()
                index.periods = period
                index.index_value = value
                index.save()
                index.index_time = index_time
                index.save()

                new_index_dic['x'].append(index_time.strftime("%H:%M"))
                new_index_dic['y'].append(str(value))

            index_day = Index_day()
            index_day.stock_id = period.stock.id
            index_day.index_value = float(data_list[-1].split(',')[1])
            index_day.save()
            index_day.created_at = date_day
            index_day.save()

            set_cache(cache_name, index_info, 86400)

            if len(new_index_dic['x']) > 0:
                guess_graph(period.id, new_index_dic)
        else:
            result_list = get_cache(cache_name)
            if len(index_info) != len(result_list):
                for data in index_info:
                    value = float(data['index_value'])
                    index_time = data['index_time']
                    flag = False

                    if data not in result_list:
                        for result_data in result_list:
                            result_index_time = result_data['index_time']
                            if index_time == result_index_time:
                                print('再次开始存储,已存储时间但数值变动')
                                print('value===> ', value)
                                print('time====>', index_time)

                                index = Index.objects.filter(periods=period, index_time=result_index_time).first()
                                index.index_value = value
                                index.save()
                                flag = True
                                break
                        if flag is True:
                            pass
                        else:
                            print('再次开始存储,新时间')
                            print('value===> ', value)
                            print('time====>', index_time)

                            index = Index()
                            index.periods = period
                            index.index_value = value
                            index.save()
                            index.index_time = index_time
                            index.save()

                            new_index_dic['x'].append(index_time.strftime("%H:%M"))
                            new_index_dic['y'].append(str(value))

                            if index_info.index(data) == len(index_info) - 1:
                                index_day = Index_day.objects.filter(stock_id=period.stock.id,
                                                                     created_at=date_day).first()
                                index_day.index_value = value
                                index_day.save()

                set_cache(cache_name, index_info, 86400)
        # 推送曲线图数据
        if len(new_index_dic['x']) > 0:
            guess_graph(period.id, new_index_dic)
    else:
        num_cache_name = Stock.STOCK[int(period.stock.name)][1] + '_' + date_ymd + '_num'
        value = index_info[-1]['index_value']
        index_time = index_info[-1]['index_time']
        index_time_str = index_info[-1]['index_time_str']
        if period.lottery_time == index_time:
            if get_cache(num_cache_name) is None:
                set_cache(num_cache_name, value + ',' + index_time_str + ',1', 3600)
            else:
                cache_dt = get_cache(num_cache_name)
                print(cache_dt)
                if cache_dt.split(',')[0] == value:
                    count = int(cache_dt.split(',')[2]) + 1
                    if count >= 6:
                        # 最后一期的确认
                        index = Index.objects.filter(periods=period, index_time=index_time).first()
                        index.index_value = value
                        index.save()

                        if float(period.start_value) > float(value):
                            status = 'down'
                        elif float(period.start_value) == float(value):
                            status = 'draw'
                        elif float(period.start_value) < float(value):
                            status = 'up'

                        param_dic = {
                            'num': value, 'status': status, 'auto': local_settings.GUESS_RESULT_AUTO,
                        }
                        guess_recording.take_result(period, param_dic, date_day)
                        return True
                    else:
                        set_cache(num_cache_name, value + ',' + index_time_str + ',' + str(count), 3600)
                else:
                    set_cache(num_cache_name, value + ',' + index_time_str + ',1', 3600)


def confirm_time(period):
    date_now = datetime.datetime.now()
    lottery_time = period.lottery_time.strftime('%Y-%m-%d %H:%M:%S')
    if period.stock.name == '0' or period.stock.name == '1':
        date_start = lottery_time.split(' ')[0] + ' ' + market_rest_cn_start_time[0]
        date_end = lottery_time.split(' ')[0] + ' ' + market_rest_cn_end_time[0]
    elif period.stock.name == '2':
        date_start = lottery_time.split(' ')[0] + ' ' + market_hk_start_time[0]
        date_end = lottery_time.split(' ')[0] + ' ' + market_hk_end_time[0]
    elif period.stock.name == '3' or period.stock.name == '4':
        date_start = lottery_time.split(' ')[0] + ' ' + market_en_start_time_winter[0]
        date_end = lottery_time.split(' ')[0] + ' ' + market_en_end_time_winter[0]

    start = datetime.datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S")
    if period.stock.name == '3' or period.stock.name == '4':
        start = start - datetime.timedelta(days=1)

    if start <= date_now <= end:
        return True
    else:
        return False


class Command(BaseCommand):
    help = "抓取证券指数"

    def handle(self, *args, **options):
        print(' now is ', datetime.datetime.now())
        if Periods.objects.filter(is_result=False).exists() is not True:
            print('暂无行情')
        else:
            """
            上证指数，深证成指
            """
            print('上证指数：')
            shang_periods = None
            if Periods.objects.filter(is_result=False, stock__name='0').exists():
                period = Periods.objects.filter(is_result=False, stock__name='0').first()
                shang_periods = period
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
                        next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
                                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
                            next_end += datetime.timedelta(1)
                            next_start += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        shang_periods = GuessRecording.newobject(str(per), period.stock_id, next_start, next_end,
                                                                 period)

            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')

            print('深证成指：')
            shen_periods = None
            if Periods.objects.filter(is_result=False, stock__name='1').exists():
                period = Periods.objects.filter(is_result=False, stock__name='1').first()
                shen_periods = period
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
                        next_start = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_start_time[0],
                                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        next_end = datetime.datetime.strptime(open_date + ' ' + market_rest_cn_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_cn_list:
                            next_end += datetime.timedelta(1)
                            next_start += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        shen_periods = GuessRecording.newobject(str(per), period.stock_id, next_start, next_end, period)
            print('------------------------------------------------------------------------------------')
            # 股指pk出题找答案,股指pk出题
            guess_pk_recording = GuessPKRecording()
            guess_pk_recording.take_pk_result(shen_periods, shang_periods, market_rest_cn_start_time[0], 1)

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
                        next_start = datetime.datetime.strptime(open_date + ' ' + market_hk_start_time[0],
                                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        next_end = datetime.datetime.strptime(open_date + ' ' + market_hk_end_time[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        while next_end.isoweekday() >= 6 or next_end.strftime('%Y-%m-%d') in market_rest_hk_dic:
                            next_end += datetime.timedelta(1)
                            next_start += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        GuessRecording.newobject(str(per), period.stock_id, next_start, next_end, period)
            print('------------------------------------------------------------------------------------')

            """
            道琼斯指数
            """
            print('道琼斯：')
            dji_periods = None
            if Periods.objects.filter(is_result=False, stock__name='3').exists():
                period = Periods.objects.filter(is_result=False, stock__name='3').first()
                dji_periods = period
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='3',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_dja = get_index_hk_en(period, url_DJA)
                    # print(dt_dja)
                    flag = get_index_en(period, url_dji)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        next_start = datetime.datetime.strptime(open_date + ' ' + market_en_start_time_winter[0],
                                                                '%Y-%m-%d %H:%M:%S')
                        next_end = datetime.datetime.strptime(open_date + ' ' + market_en_end_time_winter[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        while (next_end - datetime.timedelta(hours=12)).isoweekday() >= 6 or (
                                next_end - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in market_rest_en_dic:
                            next_end += datetime.timedelta(1)
                            next_start += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        dji_periods = GuessRecording.newobject(str(per), period.stock_id, next_start, next_end, period)
            print('------------------------------------------------------------------------------------')

            """
            纳斯达克指数
            """
            print('纳斯达克：')
            ndx_periods = None
            if Periods.objects.filter(is_result=False, stock__name='4').exists():
                period = Periods.objects.filter(is_result=False, stock__name='4').first()
                ndx_periods = period
                if (confirm_time(period) is not True) and (Periods.objects.filter(is_result=False, stock__name='4',
                                                                                  lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # dt_dja = get_index_hk_en(period, url_DJA)
                    # print(dt_dja)
                    flag = get_index_en(period, url_ndx)
                    if flag is True:
                        # 开奖后放出题目
                        print('放出题目')
                        open_date = period.lottery_time.strftime('%Y-%m-%d')
                        next_start = datetime.datetime.strptime(open_date + ' ' + market_en_start_time_winter[0],
                                                                '%Y-%m-%d %H:%M:%S')
                        next_end = datetime.datetime.strptime(open_date + ' ' + market_en_end_time_winter[0],
                                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
                        while (next_end - datetime.timedelta(hours=12)).isoweekday() >= 6 or (
                                next_end - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in market_rest_en_dic:
                            next_end += datetime.timedelta(1)
                            next_start += datetime.timedelta(1)
                        per = int(period.periods) + 1
                        ndx_periods = GuessRecording.newobject(str(per), period.stock_id, next_start, next_end, period)
            print('------------------------------------------------------------------------------------')
            guess_pk_recording = GuessPKRecording()
            guess_pk_recording.take_pk_result(ndx_periods, dji_periods, market_en_start_time_winter[0], 2)
