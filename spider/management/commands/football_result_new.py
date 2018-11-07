# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import requests
import json
from bs4 import BeautifulSoup
from quiz.models import Quiz, Rule, Option, Record, CashBackLog, OptionOdds
from users.models import UserCoin, CoinDetail, Coin, UserMessage, User, CoinPrice, CoinGive, CoinGiveRecords
from chat.models import Club
from promotion.models import PromotionRecord, UserPresentation
from utils.functions import normalize_fraction, make_insert_sql, make_batch_update_sql, to_decimal
from django.db import transaction
import datetime
from decimal import Decimal
from .asia_tb_result_new import asia_result, asia_option
from time import time
from django.db import connection
from utils.cache import get_cache, set_cache

base_url = 'https://i.sporttery.cn/api/fb_match_info/get_pool_rs/?f_callback=pool_prcess&mid='
live_url = 'https://i.sporttery.cn/api/match_info_live_2/get_match_live?m_id='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
key_football_live_dt = 'football_live_dt'


def trunc(f, n):
    s1, s2 = str(f).split('.')
    if n == 0:
        return s1
    if n <= len(s2):
        return s1 + '.' + s2[:n]
    return s1 + '.' + s2 + '0' * (n - len(s2))


def handle_activity(record, coin, earn_coin):
    # USDT活动
    quiz_list = []
    if CoinGiveRecords.objects.filter(user=record.user, coin_give__coin=coin).exists() is True:
        coin_give_records = CoinGiveRecords.objects.get(user=record.user, coin_give__coin=coin)
        if int(record.source) == Record.GIVE:
            if coin_give_records.is_recharge_lock is False:
                coin_give_records.lock_coin = Decimal(coin_give_records.lock_coin) + Decimal(earn_coin)
                coin_give_records.save()
                coin_give_records = CoinGiveRecords.objects.get(user=record.user, coin_give__coin=coin)

                for count_record in Record.objects.filter(is_distribution=True, user=record.user,
                                                          roomquiz_id=Club.objects.get(coin=coin).id,
                                                          source=str(Record.GIVE)):
                    if count_record.quiz_id not in quiz_list:
                        quiz_list.append(count_record.quiz_id)

                if (coin_give_records.lock_coin >= coin_give_records.coin_give.ask_number) and (
                        len(quiz_list) >= coin_give_records.coin_give.match_number):
                    lock_coin = coin_give_records.lock_coin
                    coin_give_records.is_recharge_lock = True
                    coin_give_records.lock_coin = 0
                    coin_give_records.save()

                    # 发送信息
                    u_mes = UserMessage()
                    u_mes.status = 0
                    u_mes.user_id = record.user_id
                    u_mes.message_id = 6  # 私人信息
                    u_mes.title = Club.objects.get(coin=coin).room_title + '活动公告'
                    u_mes.title_en = 'Notifications of upcoming Events from ' + Club.objects.get(
                        coin=coin).room_title_en
                    u_mes.content = '恭喜您获得USDT活动奖励共 ' + str(trunc(lock_coin, 2)) + 'USDT，祝贺您。'
                    u_mes.content_en = 'Congratulations on your USDT event award, ' + str(
                        trunc(lock_coin, 2)) + 'in total.Congratulations for you.'
                    u_mes.save()
        else:
            user_profit = 0
            for user_record in Record.objects.filter(user=record.user,
                                                     roomquiz_id=Club.objects.get(coin=coin).id,
                                                     source=str(Record.NORMAL),
                                                     created_at__lte=coin_give_records.coin_give.end_time,
                                                     earn_coin__gt=0):
                user_profit = user_profit + (user_record.earn_coin - user_record.bet)
            if (user_profit >= 50) and (coin_give_records.is_recharge_give is False):
                coin_give_records.is_recharge_give = True
                coin_give_records.save()

                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
                user_coin.balance = Decimal(user_coin.balance) + Decimal(10)
                user_coin.save()

                # 用户资金明细表
                coin_detail = CoinDetail()
                coin_detail.user_id = record.user_id
                coin_detail.coin_name = coin.name
                coin_detail.amount = Decimal(10)
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.ACTIVITY
                coin_detail.save()

                # 发送信息
                u_mes = UserMessage()
                u_mes.status = 0
                u_mes.user_id = record.user_id
                u_mes.message_id = 6  # 私人信息
                u_mes.title = Club.objects.get(coin=coin).room_title + '活动公告'
                u_mes.title_en = 'Notifications of upcoming Events from ' + Club.objects.get(coin=coin).room_title_en
                u_mes.content = '恭喜您获得USDT活动奖励共 10USDT，祝贺您。'
                u_mes.content_en = 'Congratulations on your USDT event award, 10 USDT in total.Congratulations for you.'
                u_mes.save()


def get_data(url):
    print('正在发起请求,竞彩网')
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print('结束请求')
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[12:-2])
            return result
    except requests.ConnectionError as e:
        print('Error', e.args)


@transaction.atomic()
def get_data_info(url, match_flag, result_data=None, host_team_score=None, guest_team_score=None):
    print('开始处理数据')
    quiz = Quiz.objects.filter(match_flag=match_flag).first()

    rule_all = Rule.objects.filter(quiz=quiz).all()
    rule_had = rule_all.filter(type=0).first()
    rule_hhad = rule_all.filter(type=1).first()
    rule_ttg = rule_all.filter(type=3).first()
    rule_crs = rule_all.filter(type=2).first()

    result_flag = False
    try:
        result_list = []
        new_url = 'http://www.310win.com/jingcaizuqiu/kaijiang_jc_all.html'
        print('正在发起请求,彩客网')
        response = requests.get(new_url, headers=headers, timeout=30)
        print('结束请求')
        soup = BeautifulSoup(response.text, 'lxml')
        data = list(soup.select('div[id="lottery_container"]')[0].children)
        for dt in data[1].find_all('tr')[1:]:
            host_team_fullname = list(dt.select('td[style="text-align:right"]')[0].strings)[0].strip().replace('\n', '')
            guest_team_fullname = dt.select('td[style="text-align:left"]')[0].string.replace(' ', '')
            score = dt.select('td[style="color:red"]')[0].b.string
            host_team_score = score.split('-')[0]
            guest_team_score = score.split('-')[1]
            ttg_list = []
            for i in range(0, 7):
                ttg_list.append(str(i))
            if (quiz.host_team_fullname == host_team_fullname or quiz.host_team == host_team_fullname) and (
                    quiz.guest_team_fullname == guest_team_fullname or quiz.guest_team == guest_team_fullname):
                quiz.host_team_score = host_team_score
                quiz.guest_team_score = guest_team_score
                quiz.save()
                for result in dt.select('span[style="color:#f00;"]')[:-1]:
                    if result.string == '负' or result.string == '胜':
                        result_list.append('主' + result.string)
                    elif result.string == '平':
                        result_list.append(result.string + '局')
                    elif result.string in ttg_list:
                        result_list.append(result.string + '球')
                    elif result.string == '7+':
                        result_list.append('7球以上')
                    else:
                        result_list.append(result.string)

                option_had = Option.objects.filter(rule=rule_had, option=result_list[1]).first()
                if option_had is not None:
                    option_had.is_right = 1

                option_hhad = Option.objects.filter(rule=rule_hhad, option=result_list[0]).first()
                if option_hhad is not None:
                    option_hhad.is_right = 1

                option_ttg = Option.objects.filter(rule=rule_ttg, option=result_list[3]).first()
                if option_ttg is not None:
                    option_ttg.is_right = 1

                option_crs = Option.objects.filter(rule=rule_crs, option=result_list[2]).first()
                if option_crs is not None:
                    option_crs.is_right = 1

                option_had.save()
                option_hhad.save()
                option_ttg.save()
                option_crs.save()

                print('result_list===========================================>', result_list)
                print('--------------------------- 彩客网路径开奖 ------------------------------')
                result_flag = True
                break
            else:
                result_flag = False
    except:
        pass

    if result_flag is False:
        if result_data is None:
            print('--------------------------- 竞彩网路径开奖 ------------------------------')
            datas = get_data(url + match_flag)
            if datas['status']['code'] == 0:
                if len(datas['result']['pool_rs']) > 0:
                    result_had = datas['result']['pool_rs'].get('had')
                    result_hhad = datas['result']['pool_rs'].get('hhad')
                    result_ttg = datas['result']['pool_rs'].get('ttg')
                    result_crs = datas['result']['pool_rs'].get('crs')
                    # result_hafu = datas['result']['pool_rs']['hafu']

                    score_status = requests.get(live_url + match_flag).json()['status']
                    score_data = requests.get(live_url + match_flag).json()['data']
                    if score_status['message'] == "no data":
                        print('no score')
                        score_url = 'http://i.sporttery.cn/api/fb_match_info/get_result_his?limit=10&is_ha=all&limit=10&c_id=0&mid=' + match_flag + '&ptype[]=three_-1&ptype[]=asia_229&&f_callback=getResultHistoryInfo'
                        response_score = requests.get(score_url, headers=headers)
                        dt = response_score.text.encode("utf-8").decode('unicode_escape')
                        score_dt = eval(dt[21:-2])
                        if score_dt['status']['code'] != 0:
                            print(score_dt['status']['message'])
                            return

                        for score in score_dt['result']['data']:
                            if score['h_cn_abbr'] == quiz.host_team and score['a_cn_abbr'] == quiz.guest_team:
                                if score['final'] != '':
                                    host_team_score = score['final'].split(':')[0]
                                    guest_team_score = score['final'].split(':')[1]
                                    print('===================================================', score['final'])
                                    break
                                else:
                                    print('really no score')
                                    print('=================================')
                                    return
                            else:
                                print('no mtach,return')
                                return
                    else:
                        host_team_score = score_data['fs_h']
                        guest_team_score = score_data['fs_a']

                    quiz.host_team_score = host_team_score
                    quiz.guest_team_score = guest_team_score
                    quiz.save()

                    if result_had is not None:
                        option_had = Option.objects.filter(rule=rule_had, flag=result_had.get('pool_rs')).first()
                        if option_had is not None:
                            option_had.is_right = 1
                            option_had.save()

                    if result_hhad is not None:
                        option_hhad = Option.objects.filter(rule=rule_hhad, flag=result_hhad.get('pool_rs')).first()
                        if option_hhad is not None:
                            option_hhad.is_right = 1
                            option_hhad.save()

                    if result_ttg is not None:
                        option_ttg = Option.objects.filter(rule=rule_ttg, flag=result_ttg.get('pool_rs')).first()
                        if option_ttg is not None:
                            option_ttg.is_right = 1
                            option_ttg.save()

                    if result_crs is not None:
                        option_crs = Option.objects.filter(rule=rule_crs, flag=result_crs.get('pool_rs')).first()
                        if option_crs is not None:
                            option_crs.is_right = 1
                            option_crs.save()

                else:
                    print(match_flag + ',' + '未有开奖信息')
                    return
            else:
                print(match_flag + ',' + '未请求到任务数据')
                return
        else:
            datas = result_data
            result_had = datas['result']['pool_rs'].get('had')
            result_hhad = datas['result']['pool_rs'].get('hhad')
            result_ttg = datas['result']['pool_rs'].get('ttg')
            result_crs = datas['result']['pool_rs'].get('crs')

            quiz.host_team_score = host_team_score
            quiz.guest_team_score = guest_team_score
            quiz.save()

            if result_had is not None:
                option_had = Option.objects.filter(rule=rule_had, flag=result_had.get('pool_rs')).first()
                if option_had is not None:
                    option_had.is_right = 1
                    option_had.save()

            if result_hhad is not None:
                option_hhad = Option.objects.filter(rule=rule_hhad, flag=result_hhad.get('pool_rs')).first()
                if option_hhad is not None:
                    option_hhad.is_right = 1
                    option_hhad.save()

            if result_ttg is not None:
                option_ttg = Option.objects.filter(rule=rule_ttg, flag=result_ttg.get('pool_rs')).first()
                if option_ttg is not None:
                    option_ttg.is_right = 1
                    option_ttg.save()

            if result_crs is not None:
                option_crs = Option.objects.filter(rule=rule_crs, flag=result_crs.get('pool_rs')).first()
                if option_crs is not None:
                    option_crs.is_right = 1
                    option_crs.save()
    else:
        pass

    # 亚盘的正确选项
    if rule_all.filter(type=8).exists():
        for rule_asia in rule_all.filter(type=8):
            asia_option(quiz, rule_asia)

    flag = False
    # 分配奖金
    records = Record.objects.filter(~Q(rule__type=str(Rule.AISA_RESULTS)), quiz=quiz, is_distribution=False)
    start_time = time()
    if len(records) > 0:
        coin_detail_list = []
        user_message_list = []
        record_right_list = []
        record_false_list = []
        user_coin_dic = {}
        i = 0

        cache_club_value = Club.objects.get_club_info()

        # 获取下注记录所有用户ID
        user_ids = []
        rule_ids = []
        option_odds_id = []
        for item in records:
            user_ids.append(item.user_id)
            rule_ids.append(item.rule_id)
            option_odds_id.append(item.option_id)
        user_ids = list(set(user_ids))  # user id去重
        rule_ids = list(set(rule_ids))  # rule id去重
        option_odds_id = list(set(option_odds_id))  # option_odds_id去重

        map_user_coin = {}
        user_coins = UserCoin.objects.filter(user_id__in=user_ids)
        for uc in user_coins:
            key = str(uc.user_id) + '_' + str(uc.coin_id)
            map_user_coin[key] = uc

        rules = Rule.objects.filter(id__in=rule_ids)
        map_rule = {}
        for rule in rules:
            map_rule[rule.id] = rule

        # 玩法对应的选项映射数据
        map_rule_option = {}
        options = Option.objects.filter(rule_id__in=rule_ids, is_right=True)
        for opt in options:
            rule_id = opt.rule_id

            opt.rule_tip = map_rule[rule_id].tips
            opt.rule_tip_en = map_rule[rule_id].tips_en
            map_rule_option[rule_id] = opt

        # option info
        option_odds = OptionOdds.objects.filter(id__in=option_odds_id)
        option_ids = []
        map_options_odd = {}
        for option_odd in option_odds:
            option_id = option_odd.option_id

            option_ids.append(option_id)
            if option_id not in map_options_odd:
                map_options_odd[option_id] = []
            map_options_odd[option_id].append(option_odd.id)

        map_option_odd_id_option = {}
        options = Option.objects.filter(id__in=option_ids)
        for option in options:
            if option.id not in map_options_odd:
                continue

            for odd_id in map_options_odd[option.id]:
                map_option_odd_id_option[odd_id] = option

        for record in records:
            user_id = record.user_id
            coin_id = cache_club_value[record.roomquiz_id]['coin_id']
            club_name = cache_club_value[record.roomquiz_id]['club_name']
            club_name_en = cache_club_value[record.roomquiz_id]['club_name_en']
            coin_name = cache_club_value[record.roomquiz_id]['coin_name']
            coin_accuracy = cache_club_value[record.roomquiz_id]['coin_accuracy']

            key_user_coin_id = str(user_id) + '_' + str(coin_id)

            flag = True
            # 判断是否回答正确
            is_right = False
            if rule_had is not None:
                if record.rule_id == rule_had.id:
                    if record.option.option_id == option_had.id:
                        is_right = True

            if rule_hhad is not None:
                if record.rule_id == rule_hhad.id:
                    if record.option.option_id == option_hhad.id:
                        is_right = True

            if rule_ttg is not None:
                if record.rule_id == rule_ttg.id:
                    if record.option.option_id == option_ttg.id:
                        is_right = True

            if rule_crs is not None:
                if record.rule_id == rule_crs.id:
                    if record.option.option_id == option_crs.id:
                        is_right = True

            # 对于用户来说，答错只是记录下注的金额
            if is_right is False:
                earn_coin = '-' + str(record.bet)
                record_false_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
            else:
                earn_coin = to_decimal(record.bet) * to_decimal(record.odds)
                earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                record_right_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})

            if is_right is True:
                # user_coin
                if record.user_id not in user_coin_dic.keys():
                    # user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                    user_coin = map_user_coin[key_user_coin_id]
                    user_coin_dic.update({
                        record.user_id: {
                            coin_id: {'balance': user_coin.balance}
                        }
                    })
                if coin_id not in user_coin_dic[record.user_id].keys():
                    # user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                    user_coin = map_user_coin[key_user_coin_id]
                    user_coin_dic[record.user_id].update({
                        coin_id: {'balance': user_coin.balance}
                    })

                user_coin_dic[user_id][coin_id]['balance'] = to_decimal(
                    user_coin_dic[user_id][coin_id]['balance']) + to_decimal(earn_coin)

                # 排除机器人
                if record.source != str(Record.CONSOLE):
                    # 用户资金明细表
                    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    coin_detail_list.append({
                        'user_id': str(user_id),
                        'coin_name': coin_name,
                        'amount': str(to_decimal(earn_coin)),
                        'rest': str(user_coin_dic[user_id][coin_id]['balance']),
                        'sources': str(CoinDetail.OPEB_PRIZE),
                        'is_delete': '0',
                        'created_at': now_time,
                    })

            # handle  USDT活动
            # if is_right is True:
            #     handle_activity(record, coin, earn_coin)
            # else:
            #     handle_activity(record, coin, 0)

            # option_right = Option.objects.get(rule=record.rule, is_right=True)
            # 排除机器人
            if record.source != str(Record.CONSOLE):
                rule_info = map_rule[record.rule_id]
                option_right = map_rule_option[record.rule_id]
                option_info = map_option_odd_id_option[record.option_id]
                title = club_name + '开奖公告'
                title_en = 'Lottery announcement from ' + club_name_en
                if is_right is False:
                    content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是：' + rule_info.tips + '  ' + option_right.option + ',您选的答案是:' + rule_info.tips + '  ' + option_info.option + '，您答错了。'
                    content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' Lottery has already been announced.The correct answer is：' + rule_info.tips_en + '-' + option_right.option_en + ',Your answer is:' + rule_info.tips_en + '-' + option_info.option_en + '，You are wrong.'
                else:
                    content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是：' + rule_info.tips + '  ' + option_right.option + ',您选的答案是:' + rule_info.tips + '  ' + option_info.option + '，您的奖金是:' + str(
                        round(earn_coin, 5))
                    content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' Lottery has already been announced.The correct answer is：' + rule_info.tips_en + '  ' + option_right.option_en + ',Your answer is:' + rule_info.tips_en + '  ' + option_info.option_en + '，Your bonus is:' + str(
                        round(earn_coin, 5))
                now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_message_list.append(
                    {
                        'user_id': str(user_id), 'status': '0',
                        'message_id': '6', 'title': title, 'title_en': title_en,
                        'content': content, 'content_en': content_en,
                        'created_at': now_time,
                    }
                )

        # 开始执行sql语句
        # 初始化sql语句
        # 插入coin_detail表
        sql = make_insert_sql('users_coindetail', coin_detail_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 插入user_message表
        sql = make_insert_sql('users_usermessage', user_message_list)
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
                              'type=\'{type}\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(type=Record.CORRECT,
                                                                             open_prize_time=now_time)
        update_record_false = 'earn_coin=VALUES(earn_coin),' \
                              'type=\'{type}\', is_distribution=\'1\', ' \
                              'open_prize_time=\'{open_prize_time}\''.format(type=Record.MISTAKE,
                                                                             open_prize_time=now_time)
        sql_right = make_batch_update_sql('quiz_record', record_right_list, update_record_right)
        sql_false = make_batch_update_sql('quiz_record', record_false_list, update_record_false)
        # print(sql_right)
        # print(sql_false)
        with connection.cursor() as cursor:
            if sql_right is not False:
                cursor.execute(sql_right)
            if sql_false is not False:
                cursor.execute(sql_false)

        # 分配亚盘奖金
        records_asia = Record.objects.filter(quiz=quiz, is_distribution=False, rule__type=str(Rule.AISA_RESULTS))
        if len(records_asia) > 0:
            asia_result(quiz, records_asia)

    quiz.status = Quiz.BONUS_DISTRIBUTION
    quiz.save()

    # 推广代理事宜
    real_records = Record.objects.filter(~Q(source=str(Record.CONSOLE)), ~Q(roomquiz_id=1), quiz=quiz,
                                         is_distribution=True)
    if len(real_records) > 0:
        PromotionRecord.objects.insert_all(real_records, 1, 1)
        UserPresentation.objects.club_flow_statistics(real_records, 1)

    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')

    end_time = time()
    cost_time = str(round(end_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)

    return flag


def handle_delay_game(delay_quiz):
    start_time = time()
    records = Record.objects.filter(quiz=delay_quiz, is_distribution=False)
    if len(records) > 0:
        coin_detail_list = []
        user_message_list = []
        user_coin_dic = {}

        cache_club_value = Club.objects.get_club_info()

        # 开始遍历record表取得信息
        i = 0
        for record in records:
            i += 1
            print('正在处理record_id为: ', record.id, ', 共 ', len(records), '条, 当前第 ', i, ' 条')
            # 延迟比赛，返回用户投注的钱
            return_coin = record.bet

            coin_id = cache_club_value[record.roomquiz_id]['coin_id']
            club_name = cache_club_value[record.roomquiz_id]['club_name']
            club_name_en = cache_club_value[record.roomquiz_id]['club_name_en']
            coin_name = cache_club_value[record.roomquiz_id]['coin_name']
            coin_accuracy = cache_club_value[record.roomquiz_id]['coin_accuracy']

            # user_coin
            if record.user_id not in user_coin_dic.keys():
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                user_coin_dic.update({
                    record.user_id: {
                        coin_id: {'balance': user_coin.balance}
                    }
                })
            if coin_id not in user_coin_dic[record.user_id].keys():
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                user_coin_dic[record.user_id].update({
                    coin_id: {'balance': user_coin.balance}
                })

            user_coin_dic[record.user_id][coin_id]['balance'] = to_decimal(user_coin_dic[record.user_id][coin_id][
                                                                               'balance']) + to_decimal(return_coin)

            # 排除机器人
            if record.source != str(Record.CONSOLE):
                # 用户资金明细表
                now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                coin_detail_list.append({
                    'user_id': str(record.user_id),
                    'coin_name': coin_name, 'amount': str(return_coin),
                    'rest': str(user_coin_dic[record.user_id][coin_id]['balance']),
                    'sources': str(CoinDetail.RETURN), 'is_delete': '0',
                    'created_at': now_time,
                })

            # 排除机器人
            if record.source != str(Record.CONSOLE):
                # 发送信息
                title = club_name + '退回公告'
                title_en = 'Return to announcement from ' + club_name_en
                content = delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 赛事延期或已中断(您的下注已全额退回)'
                content_en = delay_quiz.host_team_en + ' VS ' + delay_quiz.guest_team_en + ' The game has been postponed or has been interrupted (your wager has been fully returned)'
                now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_message_list.append(
                    {
                        'user_id': str(record.user_id), 'status': '0',
                        'message_id': '6', 'title': title, 'title_en': title_en,
                        'content': content, 'content_en': content_en,
                        'created_at': now_time,
                    }
                )

        # 开始执行sql语句
        # 插入coin_detail表
        sql = make_insert_sql('users_coindetail', coin_detail_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 插入user_message表
        sql = make_insert_sql('users_usermessage', user_message_list)
        # print(sql)
        with connection.cursor() as cursor:
            if sql is not False:
                cursor.execute(sql)

        # 更新record状态
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_record_duplicate_key = 'earn_coin=VALUES(earn_coin),' \
                                      'type=\'{type}\', is_distribution=\'1\', ' \
                                      'open_prize_time=\'{open_prize_time}\''.format(type=Record.ABNORMAL,
                                                                                     open_prize_time=now_time)
        record_list = []
        for record in records:
            earn_coin = float(record.bet)
            record_list.append({'id': str(record.id), 'earn_coin': str(earn_coin)})
        sql = make_batch_update_sql('quiz_record', record_list, update_record_duplicate_key)
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

    delay_quiz.status = Quiz.DELAY
    delay_quiz.save()

    # 推广代理事宜
    real_records = Record.objects.filter(~Q(source=str(Record.CONSOLE)), ~Q(roomquiz_id=1), quiz=delay_quiz,
                                         is_distribution=True)
    if len(real_records) > 0:
        PromotionRecord.objects.insert_all(real_records, 1, 2)
        UserPresentation.objects.club_flow_statistics(real_records, 1)

    end_time = time()
    cost_time = str(round(end_time - start_time)) + '秒'
    print('执行完成。耗时：' + cost_time)

    print(delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 返还成功！共' + str(len(records)) + '条投注记录！')


def handle_unusual_game(quiz_list):
    result_data = ''
    host_team_score = ''
    guest_team_score = ''
    for quiz in quiz_list:
        datas = get_data(base_url + quiz.match_flag)
        if len(datas['result']['pool_rs']) > 0:
            result_data = datas

        score_json = requests.get(live_url + quiz.match_flag).json()
        score_status = score_json['status']
        score_data = score_json['data']
        if score_status['message'] == "no data":
            pass
        else:
            host_team_score = score_data['fs_h']
            guest_team_score = score_data['fs_a']

    if result_data != '' and host_team_score != '' and guest_team_score != '':
        for quiz in quiz_list:
            get_data_info(base_url, quiz.match_flag, result_data, host_team_score, guest_team_score)


def cash_back(quiz):
    cash_back_rate = 0.1

    for club in Club.objects.filter(~Q(room_title='HAND俱乐部')):
        records = Record.objects.filter(quiz=quiz, roomquiz_id=club.id, user__is_robot=False)
        if len(records) > 0:
            platform_sum = 0
            profit = 0
            cash_back_sum = 0
            user_list = []
            coin_price = CoinPrice.objects.get(coin_name=club.room_title[:-3])
            for record in records:
                platform_sum = platform_sum + record.bet
                if record.earn_coin > 0:
                    profit = profit + (record.earn_coin - record.bet)
                else:
                    profit = profit + record.earn_coin
                if record.user_id not in user_list:
                    user_list.append(record.user_id)

            print('club====>' + club.room_title)
            if profit <= 0:
                print('profit====>' + str(abs(profit)))
            elif profit > 0:
                print('profit====>' + '-' + str(profit))
            print('platform_sum====>' + str(platform_sum))

            if profit < 0:
                profit_abs = abs(profit)
                for user_id in user_list:
                    personal_sum = 0
                    for record_personal in records.filter(user_id=user_id):
                        personal_sum = personal_sum + record_personal.bet
                    gsg_cash_back = float(profit_abs) * cash_back_rate * (
                            float(personal_sum) / float(platform_sum)) * (
                                            float(coin_price.price) / float(
                                        CoinPrice.objects.get(coin_name='GSG').price))
                    gsg_cash_back = trunc(gsg_cash_back, 2)
                    if float(gsg_cash_back) > 0:
                        user = User.objects.get(pk=user_id)
                        user_coin_gsg = UserCoin.objects.filter(user=user, coin_id=6).first()

                        user_coin_gsg.balance = float(user_coin_gsg.balance) + float(gsg_cash_back)
                        user_coin_gsg.save()

                        # 用户资金明细表
                        coin_detail = CoinDetail()
                        coin_detail.user_id = user_id
                        coin_detail.coin_name = "GSG"
                        coin_detail.amount = float(gsg_cash_back)
                        coin_detail.rest = user_coin_gsg.balance
                        coin_detail.sources = CoinDetail.CASHBACK
                        coin_detail.save()

                        # 发送信息
                        u_mes = UserMessage()
                        u_mes.status = 0
                        u_mes.user_id = user_id
                        u_mes.message_id = 6  # 私人信息
                        u_mes.title = club.room_title + '返现公告'
                        u_mes.title_en = 'Cash-back announcement from ' + club.room_title_en
                        u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖' + ',您得到的返现为：' + str(
                            gsg_cash_back) + '个GSG'
                        u_mes.content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' Lottery has already been announced' + ',he volume of cash-back you get is：' + str(
                            gsg_cash_back) + 'GSG'
                        u_mes.save()

                        print('use_id===>' + str(user_id) + ',cash_back====>' + str(gsg_cash_back))

                        cash_back_sum = cash_back_sum + float(gsg_cash_back)

            cash_back_log = CashBackLog()
            cash_back_log.quiz = quiz
            cash_back_log.roomquiz_id = club.id
            cash_back_log.platform_sum = platform_sum
            if profit <= 0:
                cash_back_log.profit = abs(profit)
            elif profit > 0:
                cash_back_log.profit = float('-' + str(profit))
            cash_back_log.cash_back_sum = cash_back_sum
            cash_back_log.coin_proportion = cash_back_rate
            cash_back_log.save()

            print('cash_back_sum====>' + str(cash_back_sum))
            print('---------------------------')
            quiz.is_reappearance = 1
            quiz.save()
    print('\n')


class Command(BaseCommand):
    help = "爬取足球开奖结果"

    def handle(self, *args, **options):
        print('正在执行开奖脚本...')
        print('now is ', datetime.datetime.now())
        after_24_hours = datetime.datetime.now() - datetime.timedelta(hours=24)

        if Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                               category__parent_id=2).exists():
            delay_quizs = Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                                              category__parent_id=2)

            print('检测到', len(delay_quizs), '条延迟开奖记录')
            print('----------------------------------------')

            for delay_quiz in delay_quizs:
                print('delay quiz id = ', delay_quiz.id)
                delay_quiz.status = Quiz.DELAY
                handle_delay_game(delay_quiz)
                delay_quiz.save()

                # 删除缓存中直播的数据
                football_live_dt = get_cache(key_football_live_dt)
                if delay_quiz.id in football_live_dt.keys():
                    del football_live_dt[delay_quiz.id]
                    set_cache(key_football_live_dt, football_live_dt)

        rule_data_lack = [110208, 110322, 110207, 110200, 110189, 110186, 110178, 110255, 110265, 111051]
        # 在比赛开始时间基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter(
            (Q(status=str(Quiz.PUBLISHING)) | Q(status=str(Quiz.ENDED))) & Q(begin_at__lt=after_2_hours) & Q(
                category__parent_id=2) & ~Q(match_flag__in=rule_data_lack)).order_by('id')
        if quizs.exists():
            print(len(list(quizs)))
            print(list(quizs))
            for quiz in list(quizs)[:10]:
                print('quiz.match_flag = ', quiz.match_flag)
                if int(Quiz.objects.filter(match_flag=quiz.match_flag).first().status) != Quiz.BONUS_DISTRIBUTION:
                    if quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                    guest_team=quiz.guest_team).count() >= 2:
                        handle_unusual_game(quizs.filter(begin_at=quiz.begin_at, host_team=quiz.host_team,
                                                         guest_team=quiz.guest_team))
                    else:
                        flag = get_data_info(base_url, quiz.match_flag)
                        # print(Quiz.objects.get(match_flag=quiz.match_flag).status)
                        if int(Quiz.objects.get(
                                match_flag=quiz.match_flag).status) == Quiz.BONUS_DISTRIBUTION and flag is True:
                            # cash_back(Quiz.objects.get(match_flag=quiz.match_flag))
                            pass
                # 删除缓存中直播的数据
                football_live_dt = get_cache(key_football_live_dt)
                if quiz.id in football_live_dt.keys():
                    del football_live_dt[quiz.id]
                    set_cache(key_football_live_dt, football_live_dt)
        else:
            print('暂无比赛需要开奖')
