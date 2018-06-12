# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
import datetime
import re
import requests
from bs4 import BeautifulSoup
from quiz.models import Quiz, Rule, Option, Record, CashBackLog
from users.models import UserCoin, CoinDetail, Coin, UserMessage, User, CoinPrice, CoinGiveRecords
from chat.models import Club
from decimal import Decimal

base_url = 'http://info.sporttery.cn/basketball/pool_result.php?id='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

result_match = {
    'result_mnl': {
        '主负': 'a',
        '主胜': 'h',
    },
    'result_hdc': {
        '让分主负': 'a',
        '让分主胜': 'h',
    },
    'result_wnm': {
        '主胜1-5': 'w1', '主胜6-10': 'w2', '主胜11-15': 'w3', '主胜16-20': 'w4', '主胜21-25': 'w5', '主胜26+': 'w6',
        '客胜1-5': 'l1', '客胜6-10': 'l2', '客胜11-15': 'l3', '客胜16-20': 'l4', '客胜21-25': 'l5', '客胜26+': 'l6',
    },
    'result_hilo': {
        '大': 'h',
        '小': 'l',
    },
    '未捕抓到数据': '开奖异常'
}


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

                for count_record in Record.objects.filter(user=record.user, roomquiz_id=Club.objects.get(coin=coin).id):
                    if count_record.quiz_id not in quiz_list:
                        quiz_list.append(count_record.quiz_id)

                if (coin_give_records.lock_coin >= coin_give_records.coin_give.ask_number) and (
                        datetime.datetime.now() <= coin_give_records.coin_give.end_time) and (
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
                    u_mes.content = '恭喜您获得USDT活动奖励共 ' + str(trunc(lock_coin, 2)) + 'USDT，祝贺您。'
                    u_mes.save()
        else:
            user_profit = 0
            for user_record in Record.objects.filter(user=record.user,
                                                     roomquiz_id=Club.objects.get(coin=coin).id,
                                                     source=str(Record.NORMAL),
                                                     created_at__lte=coin_give_records.coin_give.end_time,
                                                     earn_coin__gt=0):
                user_profit = user_profit + (user_record.earn_coin - user_record.bet)
            if (user_profit >= 50) and (coin_give_records.is_recharge_give is False) and (
                    datetime.datetime.now() <= coin_give_records.coin_give.end_time):
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
                u_mes.content = '恭喜您获得USDT活动奖励共 10USDT，祝贺您。'
                u_mes.save()


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.content
            return dt
    except requests.ConnectionError as e:
        print('Error', e.args)


def get_data_info(url, match_flag):
    datas = get_data(url + match_flag)
    soup = BeautifulSoup(datas, 'lxml')

    result_score = soup.select('span[class="k_bt"]')[0].string
    if len(re.findall('.*\((.*?:.*?)\)', result_score)) > 0:
        host_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][1]
        guest_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][0]

        # print(result_score)
        # print(guest_team_score + ':' + host_team_score)

        result_list = soup.select('table[class="kj-table"]')
        try:
            result_mnl = result_list[0].select('span[class="win"]')[0].string.replace(' ', '')
            result_mnl_flag = result_match['result_mnl'][result_mnl]
        except:
            print(match_flag + ',' + result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_hdc = result_list[1].select('span[class="win"]')[0].string
            result_hdc_flag = result_match['result_hdc'][result_hdc]
        except:
            print(match_flag + ',' + result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_hilo = result_list[2].select('span[class="win"]')[0].string
            result_hilo_flag = result_match['result_hilo'][result_hilo]
        except:
            print(match_flag + ',' + result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_wnm = result_list[3].select('span[class="win"]')[0].string
            result_wnm_flag = result_match['result_wnm'][result_wnm]
        except:
            print(match_flag + ',' + result_match['未捕抓到数据'])
            print('----------------------------------------')

    else:
        print(match_flag + ',' + '未有开奖信息')

    # ------------------------------------------------------------------------------------------------

    quiz = Quiz.objects.filter(match_flag=match_flag).first()
    quiz.host_team_score = host_team_score
    quiz.guest_team_score = guest_team_score
    quiz.save()

    rule_all = Rule.objects.filter(quiz=quiz).all()
    rule_mnl = rule_all.filter(type=4).first()
    rule_hdc = rule_all.filter(type=5).first()
    rule_hilo = rule_all.filter(type=6).first()
    rule_wnm = rule_all.filter(type=7).first()

    option_mnl = Option.objects.filter(rule=rule_mnl).filter(flag=result_mnl_flag).first()
    option_mnl.is_right = 1
    option_mnl.save()

    option_hdc = Option.objects.filter(rule=rule_hdc).filter(flag=result_hdc_flag).first()
    option_hdc.is_right = 1
    option_hdc.save()

    option_hilo = Option.objects.filter(rule=rule_hilo).filter(flag=result_hilo_flag).first()
    option_hilo.is_right = 1
    option_hilo.save()

    option_wnm = Option.objects.filter(rule=rule_wnm).filter(flag=result_wnm_flag).first()
    option_wnm.is_right = 1
    option_wnm.save()

    flag = False
    # 分配奖金
    records = Record.objects.filter(quiz=quiz, is_distribution=False)
    if len(records) > 0:
        for record in records:
            # 用户增加对应币金额
            club = Club.objects.get(pk=record.roomquiz_id)

            # 获取币信息
            coin = Coin.objects.get(pk=club.coin_id)

            flag = True
            # 判断是否回答正确
            is_right = False
            if record.rule_id == rule_mnl.id:
                if record.option.option_id == option_mnl.id:
                    is_right = True
            if record.rule_id == rule_hdc.id:
                if record.option.option_id == option_hdc.id:
                    is_right = True
            if record.rule_id == rule_hilo.id:
                if record.option.option_id == option_hilo.id:
                    is_right = True
            if record.rule_id == rule_wnm.id:
                if record.option.option_id == option_wnm.id:
                    is_right = True

            earn_coin = record.bet * record.odds
            record.type = Record.CORRECT
            # 对于用户来说，答错只是记录下注的金额
            if is_right is False:
                earn_coin = '-' + str(record.bet)
                record.type = Record.MISTAKE
            record.earn_coin = earn_coin
            record.save()

            if is_right is True:
                try:
                    user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
                except UserCoin.DoesNotExist:
                    user_coin = UserCoin()

                user_coin.coin_id = club.coin_id
                user_coin.user_id = record.user_id
                user_coin.balance = Decimal(user_coin.balance) + Decimal(earn_coin)
                user_coin.save()

                # 增加系统赠送锁定金额
                if int(record.source) == Record.GIVE:
                    coin_give_records = CoinGiveRecords.objects.get(user=record.user, coin_give__coin=coin)
                    coin_give_records.lock_coin = coin_give_records.lock_coin + Decimal(earn_coin)
                    coin_give_records.save()

                # 用户资金明细表
                coin_detail = CoinDetail()
                coin_detail.user_id = record.user_id
                coin_detail.coin_name = coin.name
                coin_detail.amount = Decimal(earn_coin)
                coin_detail.rest = user_coin.balance
                coin_detail.sources = CoinDetail.OPEB_PRIZE
                coin_detail.save()

            # handle  USDT活动
            if is_right is True:
                handle_activity(record, coin, earn_coin)
            else:
                handle_activity(record, coin, 0)

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = record.user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = club.room_title + '开奖公告'
            option_right = Option.objects.get(rule=record.rule, is_right=True)
            if is_right is False:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option.option + '，您答错了。'
            elif is_right is True:
                u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖，正确答案是:' + option_right.option + ',您选的答案是:' + record.option.option.option + '，您的奖金是:' + str(
                    round(earn_coin, 3))
            u_mes.save()

            record.is_distribution = True
            record.save()

    quiz.status = Quiz.BONUS_DISTRIBUTION
    quiz.save()
    print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')
    return flag


def handle_delay_game(delay_quiz):
    records = Record.objects.filter(quiz=delay_quiz, is_distribution=False)
    if len(records) > 0:
        for record in records:
            # 延迟比赛，返回用户投注的钱
            return_coin = record.bet
            record.earn_coin = return_coin
            record.type = Record.ABNORMAL
            record.save()

            # 用户增加回退还金额
            club = Club.objects.get(pk=record.roomquiz_id)

            # 获取币信息
            coin = Coin.objects.get(pk=club.coin_id)

            try:
                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
            except UserCoin.DoesNotExist:
                user_coin = UserCoin()

            user_coin.coin_id = club.coin_id
            user_coin.user_id = record.user_id
            user_coin.balance = Decimal(user_coin.balance) + Decimal(return_coin)
            user_coin.save()

            # 用户资金明细表
            coin_detail = CoinDetail()
            coin_detail.user_id = record.user_id
            coin_detail.coin_name = coin.name
            coin_detail.amount = Decimal(return_coin)
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.RETURN
            coin_detail.save()

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = record.user_id
            u_mes.message_id = 6  # 私人信息
            u_mes.title = club.room_title + '退回公告'
            u_mes.content = delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 赛事延期或已中断(您的下注已全额退回)'
            u_mes.save()

            record.is_distribution = True
            record.save()

            print(delay_quiz.host_team + ' VS ' + delay_quiz.guest_team + ' 返还成功！共' + str(len(records)) + '条投注记录！')


def cash_back(quiz):
    cash_back_rate = 0.5
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
                    gsg_cash_back = float(profit_abs) * cash_back_rate * (float(personal_sum) / float(platform_sum)) * (
                            float(coin_price.price) / float(CoinPrice.objects.get(coin_name='GSG').price))
                    gsg_cash_back = trunc(gsg_cash_back, 2)
                    if float(gsg_cash_back) > 0:
                        user = User.objects.get(pk=user_id)
                        user.integral = float(user.integral) + float(gsg_cash_back)
                        user.save()

                        # 用户资金明细表
                        coin_detail = CoinDetail()
                        coin_detail.user_id = user_id
                        coin_detail.coin_name = "GSG"
                        coin_detail.amount = float(gsg_cash_back)
                        coin_detail.rest = user.integral
                        coin_detail.sources = CoinDetail.CASHBACK
                        coin_detail.save()

                        # 发送信息
                        u_mes = UserMessage()
                        u_mes.status = 0
                        u_mes.user_id = user_id
                        u_mes.message_id = 6  # 私人信息
                        u_mes.title = club.room_title + '返现公告'
                        u_mes.content = quiz.host_team + ' VS ' + quiz.guest_team + ' 已经开奖' + ',您得到的返现为：' + str(
                            gsg_cash_back) + '个GSG'
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
    help = "爬取篮球开奖结果"

    # def add_arguments(self, parser):
    #     parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        after_24_hours = datetime.datetime.now() - datetime.timedelta(hours=24)
        if Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                               category__parent_id=2).exists():
            for delay_quiz in Quiz.objects.filter(begin_at__lt=after_24_hours, status=str(Quiz.PUBLISHING),
                                                  category__parent_id=2):
                delay_quiz.status = Quiz.DELAY
                handle_delay_game(delay_quiz)
                delay_quiz.save()

        # 在此基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter(
            (Q(status=str(Quiz.PUBLISHING)) | Q(status=str(Quiz.ENDED))) & Q(begin_at__lt=after_2_hours) & Q(
                category__parent_id=1))
        if quizs.exists():
            for quiz in quizs:
                flag = get_data_info(base_url, quiz.match_flag)
                # print(Quiz.objects.get(match_flag=quiz.match_flag).status)
                if int(Quiz.objects.get(match_flag=quiz.match_flag).status) == Quiz.BONUS_DISTRIBUTION and flag is True:
                    cash_back(Quiz.objects.get(match_flag=quiz.match_flag))
        else:
            print('暂无比赛需要开奖')
