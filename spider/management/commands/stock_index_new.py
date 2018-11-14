# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from guess.models import Index, Periods, Index_day, Issues, Stock
from .stock_result_new import GuessRecording, GuessPKRecording
import requests
import datetime
from utils.cache import *
import re
import local_settings
from guess.consumers import guess_graph

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

# 各个股票数据源地址
url_shen = 'http://www.szse.cn/api/market/ssjjhq/getTimeData?random=0.6430127918854951&marketId=1&code=399001'
url_shang = 'http://yunhq.sse.com.cn:32041/v1/sh1/line/000001?callback=jQuery111208645993247577721_1541046387829&begin=0&end=-1&select=time%2Cprice%2Cvolume'
url_djia = 'https://www.nasdaq.com/aspx/IndexData.ashx?index=ixic'
url_nasdaq = 'https://www.nasdaq.com/aspx/IndexData.ashx?index=.indu'
url_hsi = 'https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php?resource_id=8189&from_mid=1&query=%E6%81%92%E7%94%9F%E6%8C%87%E6%95%B0&hilight=disp_data.*.title&sitesign=457e1aa48b5dc5ea25a0766d5d08c047&eprop=minute'


class StockIndex(object):
    def __init__(self):
        # 2018休市日期
        self.market_rest_cn_list = ['2018-06-18', '2018-09-24', '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04',
                                    '2018-10-05']
        self.market_rest_en_dic = ['2018-09-03', '2018-11-22', '2018-12-25']
        self.market_rest_hk_dic = ['2018-09-25', '2018-10-01', '2018-10-17', '2018-12-25', '2018-12-26']

        # 开市，闭市时间点
        self.market_rest_cn_start_time = ['09:30:00']
        self.market_hk_start_time = ['09:30:00']
        self.market_en_start_time = ['21:30:00']
        self.market_en_start_time_winter = ['22:30:00']

        self.market_rest_cn_end_time = ['15:00:00']
        self.market_hk_end_time = ['16:00:00']
        self.market_en_end_time = ['04:00:00']
        self.market_en_end_time_winter = ['05:00:00']

        self.pk_periods_map = {
            # 上证 vs 深证
            Stock.SSE: None, Stock.SHENZHEN: None,
            # 道琼斯 vs 纳斯达克
            Stock.DOWJONES: None, Stock.NASDAQ: None
        }

    def fetch_data(self, stock):
        """
        从数据源获得数据并组装成字典形式
        :param stock:
        :return data_map:{'begin_time': begin_time, 'open_index': open_index, 'data_list': data_list}
        """
        # 上证指数
        if stock.name == str(Stock.SSE):
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
            if data_list[-1][0].strftime('%H:%M:%S') == self.market_rest_cn_end_time[0]:
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
            return data_map

        # 深证成指
        elif stock.name == str(Stock.SHENZHEN):
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
            if data_list[-1][0].strftime('%H:%M:%S') == self.market_rest_cn_end_time[0]:
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
            return data_map

        # 道琼斯和纳斯达克
        elif stock.name == str(Stock.DOWJONES) or stock.name == str(Stock.NASDAQ):
            if stock.name == str(Stock.DOWJONES):
                response = requests.get(url_djia, timeout=10)
            else:
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
                if index_time.strftime('%S') == '59' or index_time.strftime('%S') == '58':
                    index_time = index_time + datetime.timedelta(minutes=1)
                index_time = index_time.strftime('%Y-%m-%d %H:%M') + ':00'
                index_time = datetime.datetime.strptime(index_time, '%Y-%m-%d %H:%M:%S')
                index_value = dt['y']
                data_list.append([index_time, index_value])

            close_index = 0
            if data_list[-1][0].strftime('%H:%M:%S') == self.market_en_end_time_winter[0]:
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
            return data_map

        # 恒生指数
        elif stock.name == str(Stock.HANGSENG):
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
            return data_map

    def handle_data(self, period, data_map):
        """
        处理data_map字典数据
        :param period:
        :param data_map:
        :return:
        """
        guess_recording = GuessRecording()

        name = data_map['name']
        begin_time = data_map['begin_time']
        open_index = data_map['open_index']
        data_list = data_map['data_list']
        close_index = data_map['close_index']
        stock_name = period.stock.name

        # 判断时间是否符合股市时间
        if name == 'djia' or name == 'nasdaq':
            begin_time = datetime.datetime.strptime(begin_time, '%Y-%m-%d') + datetime.timedelta(days=1)
            begin_time = begin_time.strftime('%Y-%m-%d')
        if begin_time != period.lottery_time.strftime('%Y-%m-%d'):
            raise CommandError('警告：时间不吻合，请及时处理')

        cache_name = str(Stock.STOCK[int(stock_name)][0]) + '_' + 'period_' + str(period.id)
        date_now = datetime.datetime.now()
        date_day = datetime.datetime.strptime(period.lottery_time.strftime('%Y-%m-%d') + ' ' + '23:59:59',
                                              "%Y-%m-%d %H:%M:%S")
        new_index_dic = {'x': [], 'y': []}
        if period.start_value is None or float(period.start_value) != float(open_index):
            period.start_value = float(open_index)
            period.save()

        if date_now < period.lottery_time or \
                Index.objects.filter(periods_id=period.id, index_time=period.lottery_time).exists() is not True:
            if get_cache(cache_name) is None:
                for data in data_list:
                    index_time = data[0]
                    value = float(data[1])

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
                index_day.index_value = float(data_list[-1][1])
                index_day.save()
                index_day.created_at = date_day
                index_day.save()

                set_cache(cache_name, data_map, 24 * 60 * 60)  # 存入缓存作对比
            else:
                result_map = get_cache(cache_name)
                result_list = result_map['data_list']
                if result_map != data_map:
                    for data in data_list:
                        index_time = data[0]
                        value = float(data[1])
                        flag = False

                        # 遍历data_list,与缓存中数据做对比
                        if data not in result_list:
                            for result_data in reversed(result_list):
                                result_index_time = result_data[0]
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

                                # 储存日曲线
                                if data_list.index(data) == len(data_list) - 1:
                                    index_day = Index_day.objects.filter(stock_id=period.stock.id,
                                                                         created_at=date_day).first()
                                    index_day.index_value = value
                                    index_day.save()
                    # 最后一期再次确认，常常对不上
                    if period.stock_id in [7, 9]:
                        if data_list[-1][0].strftime('%H:%M:%S') == self.market_en_end_time_winter[0]:
                            lottery_time = period.lottery_time
                            if close_index != data_list[-1][1]:
                                index = Index.objects.filter(periods=period, index_time=lottery_time).first()
                                if index is None:
                                    index = Index()
                                    index.periods = period
                                    index.index_value = close_index
                                    index.save()
                                    index.index_time = lottery_time
                                    index.save()
                                else:
                                    index.index_value = close_index
                                    index.save()
                    set_cache(cache_name, data_map, 24 * 60 * 60)  # 存入缓存作对比
            # 推送曲线图
            if len(new_index_dic['x']) > 0:
                guess_graph(period.id, new_index_dic)
        else:
            num_cache_name = str(Stock.STOCK[int(stock_name)][0]) + '_' + begin_time + '_num'

            index_time = data_list[-1][0]
            if period.lottery_time == index_time and close_index != 0:
                if get_cache(num_cache_name) is None:
                    set_cache(num_cache_name, str(close_index) + ',' + begin_time + ',1', 3600)
                else:
                    cache_dt = get_cache(num_cache_name)
                    print(cache_dt)
                    if cache_dt.split(',')[0] == str(close_index):
                        count = int(cache_dt.split(',')[2]) + 1
                        if count >= 6:
                            # 最后一期的确认
                            index = Index.objects.filter(periods=period, index_time=index_time).first()
                            index.index_value = close_index
                            index.save()

                            status = ''
                            if float(period.start_value) > float(close_index):
                                status = 'down'
                            elif float(period.start_value) == float(close_index):
                                status = 'draw'
                            elif float(period.start_value) < float(close_index):
                                status = 'up'

                            param_dic = {
                                'num': close_index, 'status': status, 'auto': local_settings.GUESS_RESULT_AUTO,
                            }
                            guess_recording.take_result(period, param_dic, date_day)
                            return True
                        else:
                            set_cache(num_cache_name, str(close_index) + ',' + begin_time + ',' + str(count), 3600)
                    else:
                        set_cache(num_cache_name, str(close_index) + ',' + begin_time + ',1', 3600)
            else:
                print('数据不齐全，暂时不处理！')

    def confirm_time(self, period):
        """
        确认是要抓取数据还是处于空闲时间
        :param period: 股指期数对象
        :return:
        """
        date_now = datetime.datetime.now()
        lottery_time = period.lottery_time.strftime('%Y-%m-%d %H:%M:%S')
        if period.stock.name == '0' or period.stock.name == '1':
            date_start = lottery_time.split(' ')[0] + ' ' + self.market_rest_cn_start_time[0]
            date_end = lottery_time.split(' ')[0] + ' ' + self.market_rest_cn_end_time[0]
        elif period.stock.name == '2':
            date_start = lottery_time.split(' ')[0] + ' ' + self.market_hk_start_time[0]
            date_end = lottery_time.split(' ')[0] + ' ' + self.market_hk_end_time[0]
        elif period.stock.name == '3' or period.stock.name == '4':
            date_start = lottery_time.split(' ')[0] + ' ' + self.market_en_start_time_winter[0]
            date_end = lottery_time.split(' ')[0] + ' ' + self.market_en_end_time_winter[0]

        start = datetime.datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S")
        end = datetime.datetime.strptime(date_end, "%Y-%m-%d %H:%M:%S")

        if period.stock.name == '3' or period.stock.name == '4':
            start = start - datetime.timedelta(days=1)

        if start <= date_now <= end:
            return True
        else:
            return False

    def new_period(self, period):
        """
        生成新的一期
        :param period:
        :return:
        """
        # 获得不同的股市不同的开市，闭市时间段
        stock_name = period.stock.name
        if stock_name == str(Stock.SHENZHEN) or stock_name == str(Stock.SSE):
            start_hms = self.market_rest_cn_start_time[0]
            end_hms = self.market_rest_cn_end_time[0]
            rest_date = self.market_rest_cn_list
        elif stock_name == str(Stock.NASDAQ) or stock_name == str(Stock.DOWJONES):
            start_hms = self.market_en_start_time_winter[0]
            end_hms = self.market_en_end_time_winter[0]
            rest_date = self.market_rest_en_dic
        else:
            start_hms = self.market_hk_start_time[0]
            end_hms = self.market_hk_end_time[0]
            rest_date = self.market_rest_hk_dic

        open_date = period.lottery_time.strftime('%Y-%m-%d')
        next_start = datetime.datetime.strptime(open_date + ' ' + start_hms,
                                                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        next_end = datetime.datetime.strptime(open_date + ' ' + end_hms,
                                              '%Y-%m-%d %H:%M:%S') + datetime.timedelta(1)
        while (next_end - datetime.timedelta(hours=12)).isoweekday() >= 6 or (
                next_end - datetime.timedelta(hours=12)).strftime('%Y-%m-%d') in rest_date:
            next_end += datetime.timedelta(1)
            next_start += datetime.timedelta(1)
        per = int(period.periods) + 1
        self.pk_periods_map[int(stock_name)] = GuessRecording.newobject(str(per), period.stock_id, next_start, next_end,
                                                                        period)


class Command(BaseCommand):
    help = "抓取证券指数_new"

    def handle(self, *args, **options):
        print(' now is ', datetime.datetime.now())

        stock_index = StockIndex()

        for stock in Stock.objects.all():
            print(Stock.STOCK[int(stock.name)][1], ': ')
            if Periods.objects.filter(is_result=False, stock_id=stock.id).exists():
                period = Periods.objects.filter(is_result=False, stock_id=stock.id).first()
                stock_index.pk_periods_map[int(stock.name)] = period
                if (stock_index.confirm_time(period) is not True) and (
                        Periods.objects.filter(is_result=False, stock__name=stock.name,
                                               lottery_time__lt=datetime.datetime.now()).exists() is not True):
                    print('空闲时间, 空闲时间')
                else:
                    # try:
                    data_map = stock_index.fetch_data(period.stock)
                    flag = stock_index.handle_data(period, data_map)
                    # except Exception as e:
                    #     print('Error is: ', e)
                    #     continue

                    if flag is True:
                        # 开奖后放出题目
                        stock_index.new_period(period)
                        print('放出题目')
            print('==================================================================================')
        # 股指pk出题找答案,股指pk出题
        guess_pk_recording = GuessPKRecording()
        guess_pk_recording.take_pk_result(stock_index.pk_periods_map[Stock.SHENZHEN],
                                          stock_index.pk_periods_map[Stock.SSE],
                                          stock_index.market_rest_cn_start_time[0], 1)
        guess_pk_recording.take_pk_result(stock_index.pk_periods_map[Stock.NASDAQ],
                                          stock_index.pk_periods_map[Stock.DOWJONES],
                                          stock_index.market_en_start_time_winter[0], 2)
