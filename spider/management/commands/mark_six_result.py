# -*- coding: utf-8 -*-
from marksix.models import SixRecord, Option
from itertools import combinations
from utils.functions import *
from users.models import CoinDetail


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


def special_code_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = float(record.bet_coin / record.bet)
    special_code = answer_dic['code_list'][-1]
    if special_code in record.content.split(','):
        earn_coin = one_bet * float(record.odds)
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    else:
        earn_coin = float('-' + str(record.bet_coin))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def color_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = float(record.bet_coin / record.bet)
    special_color = answer_dic['color_list'][-1] + '波'
    special_color_id = str(Option.objects.get(option=special_color).id)
    if special_color_id in record.content.split(','):
        index = record.content.split(',').index(special_color_id)
        earn_coin = one_bet * float(record.odds.split(',')[index])
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    else:
        earn_coin = float('-' + str(record.bet_coin))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def continuous_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = float(record.bet_coin / record.bet)
    code_result_list = answer_dic['code_list'][:-1]
    if record.option.option == '平码':
        for code in code_result_list:
            if code in record.content.split(','):
                earn_coin = earn_coin + (one_bet * float(record.odds))
    elif record.option.option == '二中二':
        for dt in list(combinations(record.content.split(','), 2)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 2:
                earn_coin = earn_coin + (one_bet * float(record.odds))
    elif '三中二' in record.option.option:
        for dt in list(combinations(record.content.split(','), 3)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 3:
                odd = Option.objects.get(option='三中二(中三)').odds
                earn_coin = earn_coin + (one_bet * float(odd))
            elif len(right_list) == 2:
                odd = Option.objects.get(option='三中二(中二)').odds
                earn_coin = earn_coin + (one_bet * float(odd))
    elif record.option.option == '三中三':
        for dt in list(combinations(record.content.split(','), 3)):
            right_list = list(set(dt).intersection(set(code_result_list)))
            if len(right_list) == 3:
                earn_coin = earn_coin + (one_bet * float(record.odds))
    if earn_coin == 0:
        earn_coin = float('-' + str(record.bet_coin))
    else:
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def two_sides_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    result_dic = {}
    earn_coin = 0
    one_bet = float(record.bet_coin / record.bet)
    special_code = answer_dic['code_list'][-1]
    special_animal = answer_dic['chinese_zodiac_list'][-1]
    if int(special_code) == 49:
        result_dic.update({'特单双': '和局', '特大小': '和局', '合大小': '和局', '合单双': '和局'})
        record_content = record.content.split(',')
        ye_id = Option.objects.get(option='特家肖').id
        jia_id = Option.objects.get(option='特野肖').id
        if str(ye_id) in record_content:
            record_content.remove(str(ye_id))
        if str(jia_id) in record_content:
            record_content.remove(str(jia_id))
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
        if (int(special_code[0]) + int(special_code[1])) < 7:
            result_dic.update({'合大小': '总小'})
        else:
            result_dic.update({'合大小': '总大'})
        # 合单双
        if (int(special_code[0]) + int(special_code[1])) % 2 == 0:
            result_dic.update({'合单双': '总双'})
        else:
            result_dic.update({'合单双': '总单'})
    # 野家肖
    if special_animal in ['鼠', '虎', '兔', '龙', '蛇', '猴']:
        result_dic.update({'野家肖': '特野肖'})
    else:
        result_dic.update({'野家肖': '特家肖'})

    print(result_dic)

    for key, value in result_dic.items():
        if value != '和局':
            option_id = Option.objects.get(option=value).id
            if str(option_id) in record.content.split(','):
                index = record.content.split(',').index(str(option_id))
                earn_coin = earn_coin + (one_bet * float(record.odds.split(',')[index]))
    if earn_coin == 0:
        earn_coin = float('-' + str(record.bet_coin))
    else:
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def animal_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    animal_result_list = []
    one_bet = float(record.bet_coin / record.bet)
    for animal in answer_dic['chinese_zodiac_list']:
        animal_result_list.append(str(Option.objects.get(option=animal).id))
    for choose_animal in record.content.split(','):
        if choose_animal in animal_result_list:
            index = record.content.split(',').index(choose_animal)
            earn_coin = earn_coin + (one_bet * float(record.odds.split(',')[index]))
    if earn_coin == 0:
        earn_coin = float('-' + str(record.bet_coin))
    else:
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def special_head_tail_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    earn_coin = 0
    one_bet = float(record.bet_coin / record.bet)
    special_code = answer_dic['code_list'][-1]
    special_code_head = special_code[0] + '头'
    special_code_tail = special_code[1] + '尾'
    special_code_head_id = str(Option.objects.get(option=special_code_head).id)
    special_code_tail_id = str(Option.objects.get(option=special_code_tail).id)
    if special_code_head_id in record.content.split(','):
        index = record.content.split(',').index(special_code_head_id)
        earn_coin = earn_coin + (one_bet * float(record.odds.split(',')[index]))
    if special_code_tail_id in record.content.split(','):
        index = record.content.split(',').index(special_code_tail_id)
        earn_coin = earn_coin + (one_bet * float(record.odds.split(',')[index]))
    if earn_coin == 0:
        earn_coin = float('-' + str(record.bet_coin))
    else:
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def elements_result(record, answer_dic):
    # 获取币信息
    cache_club_value = Club.objects.get_club_info()
    coin_id = cache_club_value[record.club.id]['coin_id']
    coin_name = cache_club_value[record.club.id]['coin_name']
    coin_accuracy = cache_club_value[record.club.id]['coin_accuracy']

    one_bet = float(record.bet_coin / record.bet)
    special_elements = answer_dic['five_property_list'][-1]
    special_elements_id = str(Option.objects.get(option=special_elements).id)
    if special_elements_id in record.content.split(','):
        index = record.content.split(',').index(special_elements_id)
        earn_coin = one_bet * float(record.odds.split(',')[index])
        earn_coin = float(normalize_fraction(earn_coin, int(coin_accuracy)))
    else:
        earn_coin = float('-' + str(record.bet_coin))
    record.earn_coin = earn_coin
    record.save()

    base_functions(record.user_id, coin_id, coin_name, earn_coin)


def ergodic_record(issue, answer_dic):
    issue = (3 - len(issue)) * '0' + issue
    play_dic = {
        1: special_code_result, 2: color_result, 3: continuous_result, 4: two_sides_result,
        5: animal_result, 6: special_head_tail_result, 7: elements_result,
    }
    records = SixRecord.objects.filter(issue=issue, status='0')
    if len(records) > 0:
        for record in records:
            play_dic[record.play_id](record, answer_dic)
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
