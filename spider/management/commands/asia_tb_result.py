# -*- coding: utf-8 -*-

from utils.functions import normalize_fraction
from chat.models import Club
from users.models import Coin, UserCoin, CoinDetail
from quiz.models import Option, Record
from users.models import UserMessage
from decimal import Decimal
from promotion.models import PromotionRecord


def asia_option(quiz, rule_asia):
    rule_dic = {
        '平手': '0', '平手/半球': '0/0.5', '半球': '0.5', '半球/一球': '0.5/1', '一球': '1', '一球/一球半': '1/1.5',
        '一球半': '1.5', '一球半/两球': '1.5/2', '两球': '2', '两球/两球半': '2/2.5', '三球': '3', '三球/三球半': '3/3.5',
        '四球': '4',
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
        '一球半': '1.5', '球半/两球': '1.5/2', '两球': '2', '两球/两球半': '2/2.5', '三球': '3', '三球/三球半': '3/3.5',
        '四球': '4',
    }

    promotion_list = []

    for record in records_asia:
        # 用户增加对应币金额
        club = Club.objects.get(pk=record.roomquiz_id)

        # 获取币信息
        coin = Coin.objects.get(pk=club.coin_id)

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
                earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
            print('上盘全负， 下盘全胜')
        else:
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
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        print('上盘全负， 下盘全胜')

                    elif clean_score > int(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')
                else:
                    if float(clean_score) > float(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')

                    elif float(clean_score) < float(rule_dic[handicap]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = '-' + str(record.bet)
                        else:
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        print('上盘全负， 下盘全胜')

            else:
                half_one = Decimal(0.5)
                if str(clean_score) in rule_dic[handicap].split('/'):
                    if rule_dic[handicap].split('/').index(str(clean_score)) == 0:
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = normalize_fraction(record.bet * half_one, int(coin.coin_accuracy))
                        else:
                            earn_coin = (record.bet * record.odds - record.bet) * half_one + record.bet
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        print('上盘负一半， 下盘胜一半')

                    elif rule_dic[handicap].split('/').index(str(clean_score)) == 1:
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = (record.bet * record.odds - record.bet) * half_one + record.bet
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        else:
                            earn_coin = normalize_fraction(record.bet * half_one, int(coin.coin_accuracy))
                        print('上盘胜一半， 下盘输一半')

                else:
                    if float(clean_score) < float(rule_dic[handicap].split('/')[0]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = '-' + str(record.bet)
                        else:
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        print('上盘全负， 下盘全胜')

                    elif float(clean_score) > float(rule_dic[handicap].split('/')[1]):
                        if position_dic[record.option.option.option] == '上盘':
                            earn_coin = record.bet * record.odds
                            earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
                        else:
                            earn_coin = '-' + str(record.bet)
                        print('上盘全胜， 下盘全负')

        # 构建promotion_dic
        promotion_list.append({'record_id': record.id, 'source': 1, 'earn_coin': earn_coin, 'status': 1})

        record.earn_coin = earn_coin
        record.is_distribution = True
        record.save()
        if float(earn_coin) > 0:
            try:
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
            except UserCoin.DoesNotExist:
                user_coin = UserCoin()

            user_coin.coin_id = club.coin_id
            user_coin.user_id = record.user_id
            user_coin.balance = Decimal(user_coin.balance) + Decimal(earn_coin)
            user_coin.save()

            # 用户资金明细表
            coin_detail = CoinDetail()
            coin_detail.user_id = record.user_id
            coin_detail.coin_name = coin.name
            coin_detail.amount = Decimal(earn_coin)
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.OPEB_PRIZE
            coin_detail.save()

        # 发送信息
        u_mes = UserMessage()
        u_mes.status = 0
        u_mes.user_id = record.user_id
        u_mes.message_id = 6  # 私人信息
        u_mes.title = club.room_title + '开奖公告'
        u_mes.title_en = 'Lottery announcement from ' + club.room_title_en
        if float(earn_coin) < 0:
            record.type = Record.MISTAKE

            u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + '比分是：' + quiz.host_team_score + ':' + quiz.guest_team_score + ' 已经开奖，您选的是：' + record.rule.tips + '(' + record.handicap + ')' + record.option.option.option + '，您答错了。'
            u_mes.content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' result is：' + quiz.host_team_score + ':' + quiz.guest_team_score + ',Your answer is:' + record.rule.tips_en + '(' + record.handicap + ')' + record.option.option.option + '，You are wrong.'
        else:
            record.type = Record.CORRECT

            u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + '比分是：' + quiz.host_team_score + ':' + quiz.guest_team_score + ' 已经开奖，您选的是：' + record.rule.tips + '(' + record.handicap + ')' + record.option.option.option + '，您的奖金是:' + str(
                round(earn_coin, 3))
            u_mes.content_en = quiz.host_team_en + ' VS ' + quiz.guest_team_en + ' result is：' + quiz.host_team_score + ':' + quiz.guest_team_score + ',Your answer is:' + record.rule.tips_en + '(' + record.handicap + ')' + record.option.option.option + '，Your bonus is:' + str(
                round(earn_coin, 3))
        u_mes.save()

        record.is_distribution = True
        record.save()

    # 推广代理事宜
    PromotionRecord.objects.insert_all(promotion_list)
    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records_asia)) + '条亚盘投注记录！')

