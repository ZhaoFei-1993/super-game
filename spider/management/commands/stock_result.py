# -*- coding: utf-8 -*-
from guess.models import Record, Options, Periods, Index_day
from users.models import Coin, UserCoin
from utils.functions import normalize_fraction
from base.function import add_coin_detail, add_user_coin
from datetime import timedelta
from chat.models import Club

Guess_Closing = 1.5
Guess_Starting = 5


def base_functions(user_id, coin_id, earn_coin):
    add_user_coin(user_id, coin_id, earn_coin)
    add_coin_detail(user_id, coin_id, earn_coin)


def size_result(record):
    """
    玩法：大小
    """
    # 获取币信息
    coin = Coin.objects.get(pk=record.club.coin_id)
    if record.periods.size == record.options.title:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    else:
        earn_coin = '-' + str(record.bets)
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    record.save()

    base_functions(record.user_id, coin.id, earn_coin)


def points_result(record):
    """
    玩法：点数
    """
    coin = Coin.objects.get(pk=record.club.coin_id)
    num_list = record.periods.points.split(',')
    if record.options.title in num_list:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    else:
        earn_coin = '-' + str(record.bets)
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    record.save()

    base_functions(record.user_id, coin.id, earn_coin)


def pair_result(record):
    """
    玩法：对⼦
    """
    coin = Coin.objects.get(pk=record.club.coin_id)
    if record.periods.pair == record.options.title:
        earn_coin = record.bets * record.odds
        earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    else:
        earn_coin = '-' + str(record.bets)
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    record.save()

    base_functions(record.user_id, coin.id, earn_coin)


def status_result(record, win_sum_dic, lose_sum_dic):
    """
    玩法：涨跌
    """
    club_name = record.club.room_title
    lose_sum = lose_sum_dic[club_name]
    win_sum = win_sum_dic[club_name]

    coin = Coin.objects.get(pk=record.club.coin_id)
    if record.periods.up_and_down == record.options.title:
        earn_coin = lose_sum * (float(record.bets) / win_sum)
        earn_coin = normalize_fraction(earn_coin, int(coin.coin_accuracy))
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    else:
        earn_coin = '-' + str(record.bets)
        record.earn_coin = earn_coin
        record.status = Record.OPEN
    record.save()

    base_functions(record.user_id, coin.id, earn_coin)


def ergodic_record(period, dt, date):
    print(dt)
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
        club_list = []
        if period.up_and_down == '涨':
            lose_option = '跌'
        else:
            lose_option = '涨'
        for club in Club.objects.all():
            club_list.append(club.id)
            club_name = club.room_title
            win_sum_dic.update({club_name: 0})
            lose_sum_dic.update({club_name: 0})

        win_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
                                                options__title=period.up_and_down)
        lose_sum_objects = Record.objects.filter(club__in=club_list, periods=period, play__play_name=str(0),
                                                 options__title=lose_option)
        for data in win_sum_objects:
            win_sum_dic[data.club.room_title] = float(win_sum_dic[data.club.room_title]) + float(data.bets)

        for data in lose_sum_objects:
            lose_sum_dic[data.club.room_title] = float(lose_sum_dic[data.club.room_title]) + float(data.bets)

        period.save()

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
        period.points = num_spilt[0] + ',' + num_spilt[1]
        period.save()

        # 对子玩法
        if num_spilt[0] == num_spilt[1]:
            period.pair = num_spilt[0] + num_spilt[1]
            period.save()

        period.is_result = True
        period.save()

        # 开始遍历record表
        rule_dic = {
            '1': size_result, '2': points_result, '3': pair_result, '0': status_result,
        }
        for record in Record.objects.filter(periods=period, status='0'):
            if record.play.play_name == str(0):
                rule_dic[record.play.play_name](record, win_sum_dic, lose_sum_dic)
            else:
                rule_dic[record.play.play_name](record)

        # index_day = Index_day.objects.filter(stock_id=period.stock.id, created_at=date).first()
        # print(index_day.id)
        # index_day.index_value = float(dt['num'])
        # index_day.index_time = period.lottery_time
        # index_day.save()


def newobject(periods, stock_id, next_start, next_end):
    rotary_header_time = next_start - timedelta(hours=Guess_Closing)
    new_object = Periods(periods=periods, stock_id=stock_id)
    new_object.save()
    new_object.lottery_time = next_end
    new_object.rotary_header_time = rotary_header_time
    new_object.save()
