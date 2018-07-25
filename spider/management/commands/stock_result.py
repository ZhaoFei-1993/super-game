# -*- coding: utf-8 -*-
from guess.models import Record, Options
from users.models import Coin, UserCoin
from utils.functions import normalize_fraction
from base.function import add_coin_detail, add_user_coin


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


def status_result(record):
    """
    玩法：涨跌
    """
    coin = Coin.objects.get(pk=record.club.coin_id)
    if record.periods.up_and_down == record.options.title:
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


def ergodic_record(period, dt):
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

    period.save()

    # 大小玩法
    num_spilt = str(num).split('.')[1]
    num_sum = int(num_spilt[0]) + int(num_spilt[1])
    if num_sum >= 11:
        period.size = '大'
        period.size_en = 'big'
    else:
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
        rule_dic[record.play.play_name](record)

