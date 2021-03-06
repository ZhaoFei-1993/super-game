# -*- coding: utf-8 -*-
from marksix.models import SixRecord, Option, OpenPrice
from itertools import combinations
from utils.functions import *
from users.models import CoinDetail, RecordMark
from promotion.models import PromotionRecord, UserPresentation
from banker.models import BankerRecord


coin_detail_list = []
user_message_list = []
user_coin_dic = {}
record_right_list = []
record_false_list = []


def base_functions(record, coin_id, coin_name, earn_coin):
    user_id = record.user_id
    if earn_coin > 0:
        # user_coin
        if user_id not in user_coin_dic.keys():
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            user_coin_dic.update({
                user_id: {
                    coin_id: {'balance': user_coin.balance}
                }
            })
        if coin_id not in user_coin_dic[user_id].keys():
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
            user_coin_dic[user_id].update({
                coin_id: {'balance': user_coin.balance}
            })

        user_coin_dic[user_id][coin_id]['balance'] = to_decimal(
            user_coin_dic[user_id][coin_id]['balance']) + to_decimal(earn_coin)

        # 排除机器人
        if record.source != str(SixRecord.ROBOT):
            # 用户资金明细表
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            coin_detail_list.append({
                'user_id': str(user_id),
                'coin_name': coin_name, 'amount': str(earn_coin),
                'rest': str(user_coin_dic[user_id][coin_id]['balance']),
                'sources': str(CoinDetail.OPEB_PRIZE), 'is_delete': '0',
                'created_at': now_time,
            })


def special_code_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = to_decimal(record.bet_coin / record.bet)
    special_code = answer_dic['code_list'][-1]
    if special_code in record.content.split(','):
        earn_coin = one_bet * to_decimal(record.odds)
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    else:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def color_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = to_decimal(record.bet_coin / record.bet)
    special_color_id = answer_dic['special_color_id']
    if special_color_id in record.content.split(','):
        index = record.content.split(',').index(special_color_id)
        earn_coin = one_bet * to_decimal(record.odds.split(',')[index])
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    else:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def continuous_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = to_decimal(record.bet_coin / record.bet)
    code_result_list = answer_dic['code_list'][:-1]
    if record.option.option == '平码':
        for code in code_result_list:
            if code in record.content.split(','):
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
    elif record.option.option == '二中二':
        for dt in list(combinations(record.content.split(','), 2)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 2:
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
    elif '三中二' in record.option.option:
        for dt in list(combinations(record.content.split(','), 3)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 3:
                odd = Option.objects.get(option='三中二(中三)').odds
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
            elif len(right_list) == 2:
                odd = Option.objects.get(option='三中二(中二)').odds
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
    elif record.option.option == '三中三':
        for dt in list(combinations(record.content.split(','), 3)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 3:
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
    if earn_coin == 0:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    else:
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def two_sides_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    result_dic = {}
    earn_coin = 0
    one_bet = to_decimal(record.bet_coin / record.bet)
    special_code = answer_dic['code_list'][-1]
    normal_code_list = answer_dic['code_list']
    special_animal = answer_dic['chinese_zodiac_list'][-1]
    if int(special_code) == 49:
        result_dic.update({'特单双': '和局', '特大小': '和局', '总大小': '和局', '总单双': '和局'})
        record_content = record.content.split(',')
        earn_coin = earn_coin + (len(record_content) * one_bet)
    else:
        # 特大小
        if int(special_code) <= 24:
            result_dic.update({'特大小': '特小'})
        else:
            result_dic.update({'特大小': '特大'})
        # 特单双
        if int(special_code) % 2 == 0:
            result_dic.update({'特单双': '特双'})
        else:
            result_dic.update({'特单双': '特单'})
        # 合大小
        code_sum = 0
        for i in normal_code_list:
            code_sum += int(i)
        if code_sum >= 175:
            result_dic.update({'总大小': '总大'})
        else:
            result_dic.update({'总大小': '总小'})
        # 合单双
        if code_sum % 2 == 0:
            result_dic.update({'总单双': '总双'})
        else:
            result_dic.update({'总单双': '总单'})
    # 野家肖
    if special_animal in ['鼠', '虎', '兔', '龙', '蛇', '猴']:
        result_dic.update({'野家肖': '特野肖'})
    else:
        result_dic.update({'野家肖': '特家肖'})

    print(result_dic)

    for key, value in result_dic.items():
        if value != '和局':
            option_id = answer_dic['twq_side_op'][value]
            if str(option_id) in record.content.split(','):
                index = record.content.split(',').index(str(option_id))
                earn_coin = earn_coin + (one_bet * to_decimal(record.odds.split(',')[index]))

    if earn_coin == 0:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    else:
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def animal_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = to_decimal(record.bet_coin / record.bet)
    animal_result_list = answer_dic['animal_result_list']
    for choose_animal in record.content.split(','):
        if choose_animal in animal_result_list:
            index = record.content.split(',').index(choose_animal)
            earn_coin = earn_coin + (one_bet * to_decimal(record.odds.split(',')[index]))
    if earn_coin == 0:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    else:
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def special_head_tail_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = to_decimal(record.bet_coin / record.bet)
    special_code_head_id = answer_dic['special_code_head_id']
    special_code_tail_id = answer_dic['special_code_tail_id']
    if special_code_head_id in record.content.split(','):
        index = record.content.split(',').index(special_code_head_id)
        earn_coin = earn_coin + (one_bet * to_decimal(record.odds.split(',')[index]))
    if special_code_tail_id in record.content.split(','):
        index = record.content.split(',').index(special_code_tail_id)
        earn_coin = earn_coin + (one_bet * to_decimal(record.odds.split(',')[index]))
    if earn_coin == 0:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    else:
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def elements_result(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = to_decimal(record.bet_coin / record.bet)
    special_elements_id = answer_dic['special_elements_id']
    if special_elements_id in record.content.split(','):
        index = record.content.split(',').index(special_elements_id)
        earn_coin = one_bet * to_decimal(record.odds.split(',')[index])
        earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    else:
        earn_coin = to_decimal('-' + str(record.bet_coin))
    record.earn_coin = earn_coin

    base_functions(record, coin_id, coin_name, earn_coin)


def special_animal(record, answer_dic, cache_club_value):
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = to_decimal(record.bet_coin / record.bet)
    special_animal_id = answer_dic['special_animal_id']
    special_code = answer_dic['special_code']
    if special_code == '49':  # 平局
        earn_coin = record.bet_coin
    else:
        if record.option_id == 100:
            for dt in list(combinations(record.content.split(','), 6)):
                if special_animal_id in dt:
                    earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
        else:
            for dt in list(combinations(record.content.split(','), 6)):
                if special_animal_id not in dt:
                    earn_coin = earn_coin + (one_bet * to_decimal(record.odds))
        if earn_coin == 0:
            earn_coin = to_decimal('-' + str(record.bet_coin))
        else:
            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record, coin_id, coin_name, earn_coin)


def ergodic_record(issue, answer_dic, openprice_id):
    cache_club_value = Club.objects.get_club_info()
    issue = (3 - len(issue)) * '0' + issue
    play_dic = {
        1: special_code_result, 2: color_result, 3: continuous_result, 4: two_sides_result,
        5: animal_result, 6: special_head_tail_result, 7: elements_result, 8: special_animal,
    }
    records = SixRecord.objects.filter(issue=issue, status='0', open_price_id=openprice_id)
    if len(records) > 0:
        for record in records:
            play_dic[record.play_id](record, answer_dic, cache_club_value)
            record.status = '1'
            record.save()

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

    real_records = SixRecord.objects.filter(~Q(source=str(SixRecord.ROBOT)), ~Q(club_id=1), issue=issue, status='1',
                                            open_price_id=openprice_id)
    if len(real_records) > 0:
        # 推广代理事宜
        PromotionRecord.objects.insert_all(real_records, 3, 1)
        PromotionRecord.objects.club_flow_statistics(real_records, 3)

        # 公告记录标记
        RecordMark.objects.insert_all_record_mark(real_records.values_list('user_id', flat=True), 2)

        # 联合坐庄事宜
        banker_result = []
        target = {}
        profit_result = {}
        bet_sum_result = {}
        for club in Club.objects.get_all():
            target.update({club.id: {"key_id": openprice_id, "bet_sum": 0, "profit": 0, "club_id": club.id, "status": 2}})
        profit_list = real_records.values('bet_coin', 'earn_coin', 'club_id')
        for profit_dt in profit_list:
            target[profit_dt['club_id']]['bet_sum'] += profit_dt['bet_coin']
            if profit_dt['earn_coin'] < 0:
                target[profit_dt['club_id']]['profit'] += abs(profit_dt['earn_coin'])
            else:
                target[profit_dt['club_id']]['profit'] -= profit_dt['earn_coin'] - profit_dt['bet_coin']
        for key, value in target.items():
            banker_result.append(value)
            bet_sum_result.update({key: value['bet_sum']})
            profit_result.update({key: value['profit']})
        BankerRecord.objects.banker_settlement(banker_result, 3)

        # 计算盈亏
        open_price = OpenPrice.objects.get(pk=openprice_id)
        open_price.bet_sum = str(bet_sum_result)
        open_price.profit = str(profit_result)
        open_price.save()
    else:
        # 计算盈亏
        profit_result = {}
        bet_sum_result = {}
        for club in Club.objects.get_all():
            bet_sum_result.update({club.id: 0})
            profit_result.update({club.id: 0})
        open_price = OpenPrice.objects.get(pk=openprice_id)
        open_price.bet_sum = str(bet_sum_result)
        open_price.profit = str(profit_result)
        open_price.save()

