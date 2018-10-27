# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record
from users.models import CoinPrice, UserCoin, CoinDetail, Coin
from chat.models import Club
from utils.functions import normalize_fraction
from django.db.models import Q
import datetime
from utils.cache import set_cache, get_cache
from guess.models import Record as Guess_Record, RecordStockPk as Pk_Record
from marksix.models import SixRecord as Six_Record
from utils.functions import make_insert_sql, make_batch_update_sql, to_decimal, get_club_info
from django.db import connection


class CashBack(object):
    def __init__(self):
        # 分配比例
        self.rate = to_decimal(0.003)
        self.coin_detail_list = []
        self.user_message_list = []
        self.user_coin_dic = {}
        self.record_right_list = []
        self.every_day_injection_value_list = []
        self.cache_club_value = get_club_info()
        self.user_map = {}

        self.gsg_to_rmb = CoinPrice.objects.get(coin_name='GSG').price
        if to_decimal(self.gsg_to_rmb) < to_decimal(0.65):
            self.gsg_to_rmb = to_decimal(0.65)

    @staticmethod
    def cache_price():
        key_currency_coin_price = 'currency_coin_price'
        coin_price_dic = get_cache(key_currency_coin_price)
        if coin_price_dic is None:
            coin_price_dic = {}
            for coin in Coin.objects.all():
                coin_name = coin.name
                coin_price = CoinPrice.objects.get(coin_name=coin_name)
                price_rmb = coin_price.price

                coin_price = CoinPrice.objects.get(coin_name=coin_name)
                price_usd = coin_price.price_usd

                coin_price_dic.update({coin_name: {'price_rmb': price_rmb, 'price_usd': price_usd}})

            set_cache(key_currency_coin_price, coin_price_dic, 23 * 3600)
            coin_price_dic = get_cache(key_currency_coin_price)
        return coin_price_dic

    def handle_record_sum(self, record, bet_coin, club_id, coin_price_dic):
        user_id = record['user_id']
        coin_name = self.cache_club_value[club_id]['coin_name']
        is_robot = handle_is_robot(record)
        cache_price = coin_price_dic(coin_name)
        if user_id not in self.user_map:
            self.user_map.update({user_id: {'record_sum': bet_coin * to_decimal(cache_price['price_rmb']),
                                            'record_sum_usd': bet_coin * to_decimal(
                                                cache_price['price_usd']),
                                            'is_robot': is_robot, 'record_coin': {coin_name: bet_coin}}})
        else:
            self.user_map[user_id]['record_sum'] += bet_coin * to_decimal(cache_price['price_rmb'])
            self.user_map[user_id]['record_sum_usd'] += bet_coin * to_decimal(cache_price['price_usd'])
            if coin_name not in self.user_map[user_id]['record_coin']:
                self.user_map[user_id]['record_coin'][coin_name] = bet_coin
            else:
                self.user_map[user_id]['record_coin'][coin_name] += bet_coin

    def base_functions(self, user_id, coin_id, coin_name, cash_back_coin, sources):
        # user_coin
        if user_id not in self.user_coin_dic:
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            self.user_coin_dic.update({
                user_id: {
                    coin_id: {'balance': user_coin.balance}
                }
            })
        if coin_id not in self.user_coin_dic[user_id]:
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            self.user_coin_dic[user_id].update({
                coin_id: {'balance': user_coin.balance}
            })

        # 用户资金明细表
        self.user_coin_dic[user_id][coin_id]['balance'] = to_decimal(
            self.user_coin_dic[user_id][coin_id]['balance']) + to_decimal(cash_back_coin)
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.coin_detail_list.append({
            'user_id': str(user_id),
            'coin_name': coin_name, 'amount': str(cash_back_coin),
            'rest': str(self.user_coin_dic[user_id][coin_id]['balance']),
            'sources': str(sources), 'is_delete': '0',
            'created_at': now_time,
        })

    def edit_user_message(self, user_id, cash_back_coin, record_sum_usd, date_last, content_part):
        title = '返现公告'
        title_en = 'Cash-back announcement'
        content = '您在' + date_last + '投注了' + content_part + '投注总价值约为' + str(
            normalize_fraction(record_sum_usd, 2)) + 'USD ,' + '本次GSG激励数量为' + str(cash_back_coin) + '个，已发放！'
        content_en = ''
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_message_list.append(
            {
                'user_id': str(user_id), 'status': '0',
                'message_id': '6', 'title': title, 'title_en': title_en,
                'content': content, 'content_en': content_en,
                'created_at': now_time,
            }
        )

    def edit_injection_value(self, user_id, record_sum, cash_back_coin, is_robot, date_last):
        self.every_day_injection_value_list.append({
            'user_id': str(user_id), 'injection_value': str(normalize_fraction(record_sum, 8)),
            'cash_back_gsg': str(cash_back_coin), 'is_robot': str(is_robot), 'injection_time': date_last,
            'order': '0'
        })

    def cal_cash_back(self, date_last):
        # 计算完毕,开始清算
        # 返现值
        for user_id, value in self.user_map.items():
            cash_back_gsg = (to_decimal(value['record_sum']) * to_decimal(self.rate)) / to_decimal(self.gsg_to_rmb)
            cash_back_gsg = normalize_fraction(cash_back_gsg, 3)
            if cash_back_gsg > 0:
                # 返现GSG
                self.base_functions(user_id, 6, 'GSG', cash_back_gsg, CoinDetail.CASHBACK)

                # 发送信息, 组装币部分
                content_part = ''
                for coin_name, coin_sum in value['record_coin'].items():
                    content_part = content_part + str(coin_sum) + '个' + coin_name + '，'
                self.edit_user_message(user_id, cash_back_gsg, value['record_sum_usd'], date_last, content_part)

                # 组装投注价值表
                self.edit_injection_value(user_id, value['record_sum'], cash_back_gsg, value['is_robot'], date_last)

    def insert_info(self):
        # 插入coin_detail表
        sql = make_insert_sql('users_coindetail', self.coin_detail_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 更新user_coin表
        update_user_coin_duplicate_key = 'balance=VALUES(balance)'
        user_coin_list = []
        for key, value in self.user_coin_dic.items():
            for key_ch, value_ch in value.items():
                user_coin_list.append({
                    'user_id': str(key), 'coin_id': str(key_ch), 'balance': str(value_ch['balance']),
                })
        sql = make_batch_update_sql('users_usercoin', user_coin_list, update_user_coin_duplicate_key)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 插入user_message表
        sql = make_insert_sql('users_usermessage', self.user_message_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 插入EveryDayInjectionValue表
        sql = make_insert_sql('quiz_everydayinjectionvalue', self.every_day_injection_value_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)


def handle_is_robot(record):
    is_robot = 0
    if 'roomquiz_id' in record:
        if record['source'] == str(Record.CONSOLE):
            is_robot = 1
    else:
        if record['source'] == str(Six_Record.ROBOT):
            is_robot = 1
    return is_robot


class Command(BaseCommand):
    help = "计算现在用户单日投注总量,和返现"

    def handle(self, *args, **options):
        cash_back = CashBack()
        # 划分出时间区间
        date_now = datetime.datetime.now().strftime('%Y-%m-%d')
        print("date_now================", date_now)
        date_last = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        start_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                       int(date_last.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_last.split('-')[0]), int(date_last.split('-')[1]),
                                     int(date_last.split('-')[2]), 23, 59, 59)
        print(date_last, start_with, end_with, sep='\n')
        quiz_records = Record.objects.filter(~Q(roomquiz_id=Club.objects.get(room_title='HAND俱乐部').id),
                                             ~Q(roomquiz_id=Club.objects.get(room_title='DB俱乐部').id),
                                             is_distribution=True,
                                             open_prize_time__range=(start_with, end_with))
        guess_records = Guess_Record.objects.filter(~Q(club=Club.objects.get(room_title='HAND俱乐部')),
                                                    ~Q(club_id=Club.objects.get(room_title='DB俱乐部').id),
                                                    status='1', open_prize_time__range=(start_with, end_with))
        pk_records = Pk_Record.objects.filter(~Q(club=Club.objects.get(room_title='HAND俱乐部')),
                                              ~Q(club_id=Club.objects.get(room_title='DB俱乐部').id),
                                              status='1', open_prize_time__range=(start_with, end_with))
        six_records = Six_Record.objects.filter(~Q(club=Club.objects.get(room_title='HAND俱乐部')),
                                                ~Q(club_id=Club.objects.get(room_title='DB俱乐部').id),
                                                status='1', open_prize_time__range=(start_with, end_with))

        print('脚本开始', datetime.datetime.now())

        coin_price_dic = cash_back.cache_price()
        # 球赛
        for record in quiz_records.values('user_id', 'roomquiz_id', 'bet', 'source'):
            bet_coin = record['bet']
            cash_back.handle_record_sum(record, bet_coin, record['roomquiz_id'], coin_price_dic)
        # 猜股指
        for record in guess_records.values('user_id', 'club_id', 'bets', 'source'):
            bet_coin = record['bets']
            cash_back.handle_record_sum(record, bet_coin, record['club_id'], coin_price_dic)
        # 股指pk
        for record in pk_records.values('user_id', 'club_id', 'bets', 'source'):
            bet_coin = record['bets']
            cash_back.handle_record_sum(record, bet_coin, record['club_id'], coin_price_dic)
        # 六合彩
        for record in six_records.values('user_id', 'club_id', 'bets', 'source'):
            bet_coin = record['bets']
            cash_back.handle_record_sum(record, bet_coin, record['club_id'], coin_price_dic)

        print('计算record完成', datetime.datetime.now())

        # # 计算返现值
        # cash_back.cal_cash_back(date_last)
        # # 批量插入数据
        # cash_back.insert_info()

        print('脚本结束', datetime.datetime.now())

        # 兑换功能
        # i = 1
        # user_info_list = []
        # for obj in EveryDayInjectionValue.objects.filter(injection_time=date_last).order_by('-injection_value'):
        #     EXCHANGE_QUALIFICATION = "exchange_qualification_" + str(obj.user_id) + '_' + str(date_now)  # key
        #     set_cache(EXCHANGE_QUALIFICATION, i, 86400)  # 存储
        #     obj.order = i
        #     obj.save()
        #     if i <= 1000:
        #         if obj.user.is_robot == True:
        #             user_info_list.append(obj.user.id)
        #         print("i==========================", i)
        #         # # 发送信息
        #         # u_mes = UserMessage()
        #         # u_mes.status = 0
        #         # u_mes.user_id = obj.user_id
        #         # u_mes.message_id = 6  # 私人信息
        #         # u_mes.title_en = str(date_now) + 'GSG exchange qualification.'
        #         # u_mes.title = str(date_now) + 'GSG兑换资格。'
        #         # u_mes.content = '恭喜您获得了GSG的兑换资格。'
        #         # u_mes.content_en = 'Congratulations on your eligibility for GSG.'
        #         # u_mes.save()
        #     i += 1
        # EXCHANGE_QUALIFICATION_INFO = "all_exchange_qualification__info" + str(date_now)  # key
        # print("user_info_list================================", user_info_list)
        # set_cache(EXCHANGE_QUALIFICATION_INFO, user_info_list, 86400)  # 存储
        #
        # EXCHANGE_QUALIFICATION_USER_ID_NUMBER = "all_exchange_qualification__info_number" + str(date_now)  # key
        # set_cache(EXCHANGE_QUALIFICATION_USER_ID_NUMBER, len(user_info_list), 86400)  # 存储
