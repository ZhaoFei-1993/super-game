# -*- coding: utf-8 -*-
from guess.models import Options, Periods, Index_day
from guess.models import Record as Guess_Record
from datetime import timedelta
from users.models import CoinDetail
from utils.functions import *

coin_detail_list = []
user_message_list = []
user_coin_dic = {}
record_right_list = []
record_false_list = []


def base_functions(user_id, coin_id, coin_name, earn_coin):
    if Decimal(earn_coin) > 0:
        # user_coin
        if user_id not in user_coin_dic.keys():
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            user_coin_dic.update({
                user_id: {
                    coin_id: {'balance': float(user_coin.balance)}
                }
            })
        if coin_id not in user_coin_dic[user_id].keys():
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            user_coin_dic[user_id].update({
                coin_id: {'balance': float(user_coin.balance)}
            })

        # 用户资金明细表
        user_coin_dic[user_id][coin_id]['balance'] = user_coin_dic[user_id][coin_id]['balance'] + earn_coin
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        coin_detail_list.append({
            'user_id': str(user_id),
            'coin_name': coin_name, 'amount': str(float(earn_coin)),
            'rest': str(user_coin_dic[user_id][coin_id]['balance']),
            'sources': str(CoinDetail.OPEB_PRIZE), 'is_delete': '0',
            'created_at': now_time,
        })


def size_result(record):
    """
    玩法：大小
    """
    # 获取币信息
    cache_club_value = get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    if record.periods.size == record.options.title:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
    else:
        earn_coin = '-' + str(record.bets)
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def points_result(record):
    """
    玩法：点数
    """
    cache_club_value = get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    num_list = record.periods.points
    if str(record.options.title) in num_list:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
    else:
        earn_coin = '-' + str(record.bets)
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def pair_result(record):
    """
    玩法：对⼦
    """
    cache_club_value = get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    if record.periods.pair == record.options.title:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
    else:
        earn_coin = '-' + str(record.bets)
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def status_result(record, win_sum_dic, lose_sum_dic):
    """
    玩法：涨跌
    """
    cache_club_value = get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']
    club_name = cache_club_value[record.club.id]['club_name']

    lose_sum = lose_sum_dic[club_name]
    win_sum = win_sum_dic[club_name]

    if record.periods.up_and_down == record.options.title:
        earn_coin = lose_sum * (float(record.bets) / win_sum)
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
    else:
        earn_coin = '-' + str(record.bets)
        earn_coin = float(earn_coin)
        # record.earn_coin = earn_coin
        # record.status = Record.OPEN
        # 记录record
        record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def ergodic_record(period, dt, date):
    print(dt)
    print('----------------')
    if dt['auto'] is True:
        """
        遍历下注表， 填入正确选项
        """
        num = float(dt['num'])
        period.lottery_value = num
        # 涨跌玩法
        if dt['status'] == 'up':
            period.up_and_down = '涨'
            period.up_and_down_en = 'up'
        elif dt['status'] == 'down':
            period.up_and_down = '跌'
            period.up_and_down_en = 'down'
        else:
            period.up_and_down = '和'
            period.up_and_down_en = 'draw'

        # lose_sum_dic = {}
        # win_sum_dic = {}
        # if period.up_and_down == '涨':
        #     lose_option = '跌'
        # else:
        #     lose_option = '涨'
        # for club in Club.objects.all():
        #     win_sum = Record.objects.filter(club=club, periods=period, play__play_name=str(0),
        #                                     options__title=period.up_and_down).aggregate(Sum('bets'))
        #     lose_sum = Record.objects.filter(club=club, periods=period, play__play_name=str(0),
        #                                      options__title=lose_option).aggregate(Sum('bets'))
        #     win_bet_sum = float(win_sum['bets__sum'])
        #     lose_bet_sum = float(lose_sum['bets__sum'])
        #
        #     club_name = club.room_title
        #     lose_sum_dic.update({club_name: lose_bet_sum})
        #     win_sum_dic.update({club_name: win_bet_sum})

        win_sum_dic = {}
        lose_sum_dic = {}
        # club_list = []
        # if period.up_and_down == '涨':
        #     lose_option = '跌'
        # else:
        #     lose_option = '涨'
        # for club in Club.objects.all():
        #     club_list.append(club.id)
        #     club_name = club.room_title
        #     win_sum_dic.update({club_name: 0})
        #     lose_sum_dic.update({club_name: 0})
        #
        # win_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
        #                                         options__title=period.up_and_down)
        # lose_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
        #                                          options__title=lose_option)
        # for data in win_sum_objects:
        #     win_sum_dic[data.club.room_title] = float(win_sum_dic[data.club.room_title]) + float(data.bets)
        #
        # for data in lose_sum_objects:
        #     lose_sum_dic[data.club.room_title] = float(lose_sum_dic[data.club.room_title]) + float(data.bets)
        #
        # period.save()

        # 大小玩法
        num_spilt = str(dt['num']).split('.')[1]
        num_sum = int(num_spilt[1])
        if num_sum >= 5:
            period.size = '大'
            period.size_en = 'big'
        elif num_sum < 5:
            period.size = '小'
            period.size_en = 'small'
        period.save()

        # 点数玩法
        period.points = num_spilt[0] + num_spilt[1]
        period.save()

        # 对子玩法
        if num_spilt[0] == num_spilt[1]:
            period.pair = num_spilt[0] + num_spilt[1]
            period.save()

        # 开始遍历record表
        i = 0
        rule_dic = {
            '1': size_result, '2': points_result, '3': pair_result, '0': status_result,
        }
        records = Guess_Record.objects.filter(periods=period, status='0')
        if len(records) > 0:
            for record in records:
                i += 1
                print('正在处理record_id为: ', record.id, ', 共 ', len(records), '条, 当前第 ', i, ' 条')
                if record.play.play_name == str(0):
                    rule_dic[record.play.play_name](record, win_sum_dic, lose_sum_dic)
                else:
                    rule_dic[record.play.play_name](record)

        # 开始执行sql语句
        # 插入coin_detail表
        sql = make_insert_sql('users_coindetail', coin_detail_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 更新user_coin表
        update_user_coin_duplicate_key = 'balance=VALUES(balance)'
        user_coin_list = []
        for key, value in user_coin_dic.items():
            for key_ch, value_ch in value.items():
                user_coin_list.append({
                    'user_id': str(key), 'coin_id': str(key_ch), 'balance': str(value_ch['balance']),
                })
        sql = make_batch_update_sql('users_usercoin', user_coin_list, update_user_coin_duplicate_key)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 更新record状态
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_record_right = 'earn_coin=VALUES(earn_coin),' \
                              'status=\'1\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(open_prize_time=now_time)
        update_record_false = 'earn_coin=VALUES(earn_coin),' \
                              'status=\'1\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(open_prize_time=now_time)
        sql_right = make_batch_update_sql('guess_record', record_right_list, update_record_right)
        sql_false = make_batch_update_sql('guess_record', record_false_list, update_record_false)
        # print(sql_right)
        # print(sql_false)
        with connection.cursor() as cursor:
            if sql_right is not False:
                cursor.execute(sql_right)
            if sql_false is not False:
                cursor.execute(sql_false)

        # index_day = Index_day.objects.filter(stock_id=period.stock.id, created_at=date).first()
        # index_day.index_value = float(dt['num'])
        # index_day.index_time = period.lottery_time
        # index_day.save()

        period.is_result = True
        period.save()


def newobject(periods, stock_id, next_start, next_end):
    rotary_header_time = next_end - timedelta(minutes=30)
    new_object = Periods(periods=periods, stock_id=stock_id)
    new_object.save()
    new_object.lottery_time = next_end
    new_object.rotary_header_time = rotary_header_time
    new_object.save()
