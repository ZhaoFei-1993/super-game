# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
import requests
import json
from quiz.models import Quiz, Rule, Option, Record
from users.models import UserCoin, CoinDetail, Coin
from chat.models import Club
from django.db import transaction
import datetime
from decimal import Decimal

base_url = 'http://i.sporttery.cn/api/fb_match_info/get_pool_rs/?f_callback=pool_prcess&mid='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[12:-2])
            return result
    except requests.ConnectionError as e:
        print('Error', e.args)


@transaction.atomic()
def get_data_info(url, match_flag, quiz):
    if quiz.category.parent_id == 2:
        datas = get_data(url + match_flag)
        if datas['status']['code'] == 0:
            if len(datas['result']['pool_rs']) > 0:
                result_had = datas['result']['pool_rs']['had']
                result_hhad = datas['result']['pool_rs']['hhad']
                result_ttg = datas['result']['pool_rs']['ttg']
                result_crs = datas['result']['pool_rs']['crs']
                # result_hafu = datas['result']['pool_rs']['hafu']

                score = result_crs['prs_name'].split(':')
                if len(score) < 2:
                    return True

                host_team_score, guest_team_score = score

                quiz = Quiz.objects.filter(match_flag=match_flag).first()
                quiz.host_team_score = host_team_score
                quiz.guest_team_score = guest_team_score
                quiz.status = quiz.PUBLISHING_ANSWER
                quiz.save()

                rule_all = Rule.objects.filter(quiz=quiz).all()
                rule_had = rule_all.filter(type=0).first()
                rule_hhad = rule_all.filter(type=1).first()
                rule_ttg = rule_all.filter(type=3).first()
                rule_crs = rule_all.filter(type=2).first()

                option_had = Option.objects.filter(rule=rule_had).filter(flag=result_had['pool_rs']).first()
                if option_had is not None:
                    option_had.is_right = 1
                    option_had.save()

                option_hhad = Option.objects.filter(rule=rule_hhad).filter(flag=result_hhad['pool_rs']).first()
                if option_hhad is not None:
                    option_hhad.is_right = 1
                    option_hhad.save()

                option_ttg = Option.objects.filter(rule=rule_ttg).filter(flag=result_ttg['pool_rs']).first()
                if option_ttg is not None:
                    option_ttg.is_right = 1
                    option_ttg.save()

                option_crs = Option.objects.filter(rule=rule_crs).filter(flag=result_crs['pool_rs']).first()
                if option_crs is not None:
                    option_crs.is_right = 1
                    option_crs.save()

                # 分配奖金
                records = Record.objects.filter(quiz=quiz)
                if len(records) > 0:
                    for record in records:
                        # 判断是否回答正确
                        is_right = False
                        if record.rule_id == rule_had.id:
                            if record.option_id == option_had.id:
                                is_right = True
                        if record.rule_id == rule_hhad.id:
                            if record.option_id == option_hhad.id:
                                is_right = True
                        if record.rule_id == rule_ttg.id:
                            if record.option_id == option_ttg.id:
                                is_right = True
                        if record.rule_id == rule_crs.id:
                            if record.option_id == option_crs.id:
                                is_right = True

                        earn_coin = record.bet * record.odds
                        # 对于用户来说，答错只是记录下注的金额
                        if is_right is False:
                            earn_coin = '-' + str(record.bet)
                        record.earn_coin = earn_coin
                        record.save()

                        if is_right is True:
                            # 用户增加对应币金额
                            club = Club.objects.get(pk=record.roomquiz_id)

                            # 获取币信息
                            coin = Coin.objects.get(pk=club.coin_id)

                            try:
                                user_coin = UserCoin.objects.get(user_id=record.user_id, coin=coin)
                            except UserCoin.DoesNotExist:
                                user_coin = UserCoin()

                            user_coin.coin_id = club.coin_id
                            user_coin.user_id = record.user_id
                            user_coin.balance += Decimal(earn_coin)
                            user_coin.save()

                            # 用户资金明细表
                            coin_detail = CoinDetail()
                            coin_detail.user_id = record.user_id
                            coin_detail.coin_name = coin.name
                            coin_detail.amount = Decimal(earn_coin)
                            coin_detail.rest = user_coin.balance
                            coin_detail.sources = CoinDetail.BETS
                            coin_detail.save()
                quiz.status = Quiz.BONUS_DISTRIBUTION
                print(quiz.host_team + ' VS ' + quiz.guest_team + ' 开奖成功！共' + str(len(records)) + '条投注记录！')

            else:
                print(match_flag + ',' + '未有开奖信息')
        else:
            print(match_flag + ',' + '未请求到任务数据')


class Command(BaseCommand):
    help = "爬取足球开奖结果"

    # def add_arguments(self, parser):
    #     parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        # 在此基础上增加2小时
        after_2_hours = datetime.datetime.now() - datetime.timedelta(hours=2)
        quizs = Quiz.objects.filter((Q(status=Quiz.PUBLISHING) | Q(status=Quiz.ENDED)) & Q(begin_at__lt=after_2_hours))
        for quiz in quizs:
            get_data_info(base_url, quiz.match_flag, quiz)
