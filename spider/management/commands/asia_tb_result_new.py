# -*- coding: utf-8 -*-

from utils.functions import *
from chat.models import Club
from users.models import Coin, UserCoin, CoinDetail
from quiz.models import Option, Record
from users.models import UserMessage
from decimal import Decimal


def asia_option(quiz, rule_asia):
    rule_dic = {
        '平手': '0', '平手/半球': '0/0.5', '半球': '0.5', '半球/一球': '0.5/1', '一球': '1',
        '一球/一球半': '1/1.5', '一球半': '1.5', '一球半/两球': '1.5/2', '两球': '2', '两球/两球半': '2/2.5',
        '两球半': '2.5',  '三球': '3', '三球/三球半': '3/3.5', '三球半': '3.5', '四球': '4',
    }

    handicap = rule_asia.handicap.replace('受让', '')
    host_team_score = int(quiz.host_team_score)
    guest_team_score = int(quiz.guest_team_score)
    if '受让' in rule_asia.handicap:
        clean_score = guest_team_score - host_team_score
        position_dic = {'下盘': '主队', '上盘': '客队'}
    else:
        clean_score = host_team_score - guest_team_score
        position_dic = {'上盘': '主队', '下盘': '客队'}

    if clean_score < 0:
        option = Option.objects.get(rule=rule_asia, option=position_dic['下盘'])
        option.is_right = True
        option.save()
        print('上盘全负， 下盘全胜')
    else:
        if len(rule_dic[handicap].split('/')) == 1:
            if len(rule_dic[handicap]) == 1:
                if clean_score == int(rule_dic[handicap]):
                    option_home = Option.objects.get(rule=rule_asia, order=1)
                    option_home.is_right = True
                    option_home.save()
                    option_guest = Option.objects.get(rule=rule_asia, order=2)
                    option_guest.is_right = True
                    option_guest.save()
                    print('上，下 退还本金')

                elif clean_score < int(rule_dic[handicap]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['下盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全负， 下盘全胜')

                elif clean_score > int(rule_dic[handicap]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['上盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全胜， 下盘全负')
            else:
                if float(clean_score) > float(rule_dic[handicap]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['上盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全胜， 下盘全负')

                elif float(clean_score) < float(rule_dic[handicap]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['下盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全负， 下盘全胜')

        else:
            if str(clean_score) in rule_dic[handicap].split('/'):
                if rule_dic[handicap].split('/').index(str(clean_score)) == 0:
                    option = Option.objects.get(rule=rule_asia, option=position_dic['下盘'])
                    option.is_right = True
                    option.save()
                    print('上盘负一半， 下盘胜一半')

                elif rule_dic[handicap].split('/').index(str(clean_score)) == 1:
                    option = Option.objects.get(rule=rule_asia, option=position_dic['上盘'])
                    option.is_right = True
                    option.save()
                    print('上盘胜一半， 下盘输一半')

            else:
                if float(clean_score) < float(rule_dic[handicap].split('/')[0]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['下盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全负， 下盘全胜')

                elif float(clean_score) > float(rule_dic[handicap].split('/')[1]):
                    option = Option.objects.get(rule=rule_asia, option=position_dic['上盘'])
                    option.is_right = True
                    option.save()
                    print('上盘全胜， 下盘全负')


def asia_result(quiz, records_asia):
    rule_dic = {
        '平手': '0', '平手/半球': '0/0.5', '半球': '0.5', '半球/一球': '0.5/1', '一球': '1', '一球/一球半': '1/1.5',
        '一球半': '1.5', '一球半/两球': '1.5/2', '两球': '2', '两球/两球半': '2/2.5', '三球': '3', '三球/三球半': '3/3.5',
        '四球': '4',
    }

    coin_detail_list = []
    user_message_list = []
    user_coin_dic = {}
    i = 0
    print('共 ', len(records_asia), ' 条投注记录')
    for record in records_asia:
        # i += 1
        # print('正在处理record_id为: ', record.id, ', 共 ', len(records_asia), '条, 当前第 ', i, ' 条 (亚盘)')
        cache_club_value = Club.objects.get_club_info()
        coin_id = cache_club_value[record.roomquiz_id]['coin_id']
        club_name = cache_club_value[record.roomquiz_id]['club_name']
        club_name_en = cache_club_value[record.roomquiz_id]['club_name_en']
        coin_name = cache_club_value[record.roomquiz_id]['coin_name']
        coin_accuracy = cache_club_value[record.roomquiz_id]['coin_accuracy']

        handicap = record.handicap.replace('受让', '')
        host_team_score = int(quiz.host_team_score)
        guest_team_score = int(quiz.guest_team_score)

        if '受让' in record.handicap:
            clean_score = guest_team_score - host_team_score
            position_dic = {'主队': '下盘', '客队': '上盘'}
        else:
            clean_score = host_team_score - guest_team_score
            position_dic = {'主队': '上盘', '客队': '下盘'}

        if clean_score < 0:
            if position_dic[record.option.option.option] == '上盘':
                earn_coin = '-' + str(record.bet)
            else:
                earn_coin = record.bet * record.odds
                earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
            print('上盘全负， 下盘全胜')
        else:
            print(handicap)
            print(rule_dic[handicap])
            if len(rule_dic[handicap].split('/')) == 1:
                if len(rule_dic[handicap]) == 1:
                    if clean_score == int(rule_dic[handicap]):
                        earn_coin = record.bet
                        print('上，下 退还本金')

                    elif clean_score < int(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = '-' + str(record.bet)
                        else:
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        print('上盘全负， 下盘全胜')

                    elif clean_score > int(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')
                else:
                    if float(clean_score) > float(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')

                    elif float(clean_score) < float(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = '-' + str(record.bet)
                        else:
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        print('上盘全负， 下盘全胜')

            else:
                half_one = Decimal(0.5)
                if str(clean_score) in rule_dic[handicap].split('/'):
                    if rule_dic[handicap].split('/').index(str(clean_score)) == 0:
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = normalize_fraction(record.bet * half_one, int(coin_accuracy))
                        else:
                            earn_coin = (record.bet * record.odds - record.bet) * half_one + record.bet
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        print('上盘负一半， 下盘胜一半')

                    elif rule_dic[handicap].split('/').index(str(clean_score)) == 1:
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = (record.bet * record.odds - record.bet) * half_one + record.bet
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        else:
                            earn_coin = normalize_fraction(record.bet * half_one, int(coin_accuracy))
                        print('上盘胜一半， 下盘输一半')

                else:
                    if float(clean_score) < float(rule_dic[handicap].split('/')[0]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = '-' + str(record.bet)
                        else:
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        print('上盘全负， 下盘全胜')

                    elif float(clean_score) > float(rule_dic[handicap].split('/')[1]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')

        earn_coin = float(earn_coin)
        if earn_coin > 0:
            if record.user_id not in user_coin_dic.keys():
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                user_coin_dic.update({
                    record.user_id: {
                        coin_id: {'balance': float(user_coin.balance)}
                    }
                })
            if coin_id not in user_coin_dic[record.user_id].keys():
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin_id=coin_id)
                user_coin_dic[record.user_id].update({
                    coin_id: {'balance': float(user_coin.balance)}
                })

            # 用户资金明细表
            user_coin_dic[record.user_id][coin_id]['balance'] = user_coin_dic[record.user_id][coin_id][
                                                                    'balance'] + earn_coin
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            coin_detail_list.append({
                'user_id': str(record.user_id),
                'coin_name': coin_name, 'amount': str(float(earn_coin)),
                'rest': str(user_coin_dic[record.user_id][coin_id]['balance']),
                'sources': str(CoinDetail.OPEB_PRIZE), 'is_delete': '0',
                'created_at': now_time,
            })

        # 发送信息
        title = club_name + '开奖公告'
        title_en = 'Lottery announcement from' + club_name_en
        if earn_coin < 0:
            content = quiz.host_team + ' VS ' + quiz.guest_team + '比分是：' + str(quiz.host_team_score) + ':' + str(quiz.guest_team_score) + ' 已经开奖，您选的是：' + record.rule.tips + '(' + record.handicap + ')' + record.option.option.option + '，您答错了。'
            content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' result is：' + str(quiz.host_team_score) + ':' + str(quiz.guest_team_score) + ',Your answer is:' + record.rule.tips_en + '(' + record.handicap + ')' + record.option.option.option + '，You are wrong.'
        else:
            content = quiz.host_team + ' VS ' + quiz.guest_team + '比分是：' + str(quiz.host_team_score) + ':' + str(quiz.guest_team_score) + ' 已经开奖，您选的是：' + record.rule.tips + '(' + record.handicap + ')' + record.option.option.option + '，您的奖金是:' + str(
                round(earn_coin, 3))
            content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' result is：' + str(quiz.host_team_score) + ':' + str(quiz.guest_team_score) + ',Your answer is:' + record.rule.tips_en + '(' + record.handicap + ')' + record.option.option.option + '，Your bonus is:' + str(
                round(earn_coin, 3))
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_message_list.append(
            {
                'user_id': str(record.user_id), 'status': '0',
                'message_id': '6', 'title': title, 'title_en': title_en,
                'content': content, 'content_en': content_en,
                'created_at': now_time,
            }
        )

        record.earn_coin = earn_coin
        record.is_distribution = True
        record.save()

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
            if sql is not False:
                cursor.execute(sql)

    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records_asia)) + '条亚盘投注记录！')
