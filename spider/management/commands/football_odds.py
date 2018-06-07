# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
import os
import requests
import json
from .get_time import get_time
from quiz.models import Quiz, Rule, Option, QuizOddsLog, OptionOdds
from chat.models import Club

base_url = 'http://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=had&poolcode[]=hhad&poolcode[]=ttg&poolcode[]=crs&poolcode[]=hafu'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def update_odds(result, rule, quiz, change_time, flag):
    mark = False
    for dt in result:
        if flag == 1:
            guest_let_score = 0
            home_let_score = 0
            if dt[1][0] == '+':
                guest_let_score = dt[1][1]
            else:
                home_let_score = dt[1][1]

            option = Option.objects.get(rule=rule, flag=dt[0])
            if float(option.odds) != float(dt[2]) or float(guest_let_score) != float(rule.guest_let_score) or float(
                    home_let_score) != float(rule.home_let_score):
                mark = True
                break
        else:
            option = Option.objects.get(rule=rule, flag=dt[0])
            if float(option.odds) != float(dt[2]):
                mark = True
                break

    if mark is True:
        for dt in result:
            if flag == 1:
                guest_let_score = 0
                home_let_score = 0
                if dt[1][0] == '+':
                    guest_let_score = dt[1][1]
                else:
                    home_let_score = dt[1][1]
                option = Option.objects.get(rule=rule, flag=dt[0])
                quiz_odds_log = QuizOddsLog()
                quiz_odds_log.quiz = quiz
                quiz_odds_log.rule = rule
                quiz_odds_log.option = option
                quiz_odds_log.option_title = option.option
                quiz_odds_log.odds = dt[2]
                quiz_odds_log.change_at = change_time
                quiz_odds_log.save()
                # 对应选项赔率相应变化
                option.odds = dt[2]
                option.save()

                rule.home_let_score = float(home_let_score)
                rule.guest_let_score = float(guest_let_score)
                rule.save()

                clubs = Club.objects.all()
                for club in clubs:
                    option_odds = OptionOdds.objects.get(club=club, quiz=quiz, option=option)
                    option_odds.odds = dt[2]
                    option_odds.save()
            else:
                option = Option.objects.get(rule=rule, flag=dt[0])
                quiz_odds_log = QuizOddsLog()
                quiz_odds_log.quiz = quiz
                quiz_odds_log.rule = rule
                quiz_odds_log.option = option
                quiz_odds_log.option_title = option.option
                quiz_odds_log.odds = dt[2]
                quiz_odds_log.change_at = change_time
                quiz_odds_log.save()
                # 对应选项赔率相应变化
                option.odds = dt[2]
                option.save()

                clubs = Club.objects.all()
                for club in clubs:
                    option_odds = OptionOdds.objects.get(club=club, quiz=quiz, option=option)
                    option_odds.odds = dt[2]
                    option_odds.save()
        print(quiz.match_flag + ',' + quiz.host_team + 'VS' + quiz.guest_team + '的玩法:' + rule.tips + ',赔率已变化')
        print('=================================================')
    else:
        pass


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[8:-2])
            return result
    except requests.ConnectionError as e:
        print('Error', e.args)


def get_data_info(url):
    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            match_id = data[1].get('id')

            option_data_had = data[1].get('had')
            result_had = []
            if option_data_had:
                title_a_had = '主负'
                title_d_had = '平局'
                title_h_had = '主胜'
                odd_a_had = option_data_had['a']
                odd_d_had = option_data_had['d']
                odd_h_had = option_data_had['h']
                flag_a_had = 'a'
                flag_d_had = 'd'
                flag_h_had = 'h'
                result_had = [(flag_h_had, title_h_had, odd_h_had), (flag_d_had, title_d_had, odd_d_had),
                              (flag_a_had, title_a_had, odd_a_had)]

            option_data_hhad = data[1].get('hhad')
            result_hhad = []
            if option_data_hhad:
                title_a_hhad = option_data_hhad['fixedodds'] + '主负'
                title_d_hhad = option_data_hhad['fixedodds'] + '平局'
                title_h_hhad = option_data_hhad['fixedodds'] + '主胜'
                odd_a_hhad = option_data_hhad['a']
                odd_d_hhad = option_data_hhad['d']
                odd_h_hhad = option_data_hhad['h']
                flag_a_hhad = 'a'
                flag_d_hhad = 'd'
                flag_h_hhad = 'h'
                result_hhad = [(flag_h_hhad, title_h_hhad, odd_h_hhad), (flag_d_hhad, title_d_hhad, odd_d_hhad),
                               (flag_a_hhad, title_a_hhad, odd_a_hhad)]

            option_data_ttg = data[1].get('ttg')
            result_ttg = []
            if option_data_ttg:
                title_s0 = '0球'
                title_s1 = '1球'
                title_s2 = '2球'
                title_s3 = '3球'
                title_s4 = '4球'
                title_s5 = '5球'
                title_s6 = '6球'
                title_s7 = '7球以上'

                odd_s0 = option_data_ttg['s0']
                odd_s1 = option_data_ttg['s1']
                odd_s2 = option_data_ttg['s2']
                odd_s3 = option_data_ttg['s3']
                odd_s4 = option_data_ttg['s4']
                odd_s5 = option_data_ttg['s5']
                odd_s6 = option_data_ttg['s6']
                odd_s7 = option_data_ttg['s7']

                flag_s0 = 's0'
                flag_s1 = 's1'
                flag_s2 = 's2'
                flag_s3 = 's3'
                flag_s4 = 's4'
                flag_s5 = 's5'
                flag_s6 = 's6'
                flag_s7 = 's7'
                result_ttg = [(flag_s0, title_s0, odd_s0), (flag_s1, title_s1, odd_s1), (flag_s2, title_s2, odd_s2),
                              (flag_s3, title_s3, odd_s3), (flag_s4, title_s4, odd_s4), (flag_s5, title_s5, odd_s5),
                              (flag_s6, title_s6, odd_s6), (flag_s7, title_s7, odd_s7)]

            option_data_crs = data[1].get('crs')
            result_crs = []
            if option_data_crs:
                title_10 = '1:0'
                title_20 = '2:0'
                title_21 = '2:1'
                title_30 = '3:0'
                title_31 = '3:1'
                title_32 = '3:2'
                title_40 = '4:0'
                title_41 = '4:1'
                title_42 = '4:2'
                title_50 = '5:0'
                title_51 = '5:1'
                title_52 = '5:2'
                title_hh = '胜其他'

                title_00 = '0:0'
                title_11 = '1:1'
                title_22 = '2:2'
                title_33 = '3:3'
                title_dd = '平其他'

                title_01 = '0:1'
                title_02 = '0:2'
                title_12 = '1:2'
                title_03 = '0:3'
                title_13 = '1:3'
                title_23 = '2:3'
                title_04 = '0:4'
                title_14 = '1:4'
                title_24 = '2:4'
                title_05 = '0:5'
                title_15 = '1:5'
                title_25 = '2:5'
                title_aa = '负其他'
                # ------------------------------------------
                odd_10 = option_data_crs['0100']
                odd_20 = option_data_crs['0200']
                odd_21 = option_data_crs['0201']
                odd_30 = option_data_crs['0300']
                odd_31 = option_data_crs['0301']
                odd_32 = option_data_crs['0302']
                odd_40 = option_data_crs['0400']
                odd_41 = option_data_crs['0401']
                odd_42 = option_data_crs['0402']
                odd_50 = option_data_crs['0500']
                odd_51 = option_data_crs['0501']
                odd_52 = option_data_crs['0502']
                odd_hh = option_data_crs['-1-h']

                odd_00 = option_data_crs['0000']
                odd_11 = option_data_crs['0101']
                odd_22 = option_data_crs['0202']
                odd_33 = option_data_crs['0303']
                odd_dd = option_data_crs['-1-d']

                odd_01 = option_data_crs['0001']
                odd_02 = option_data_crs['0002']
                odd_12 = option_data_crs['0102']
                odd_03 = option_data_crs['0003']
                odd_13 = option_data_crs['0103']
                odd_23 = option_data_crs['0203']
                odd_04 = option_data_crs['0004']
                odd_14 = option_data_crs['0104']
                odd_24 = option_data_crs['0204']
                odd_05 = option_data_crs['0005']
                odd_15 = option_data_crs['0105']
                odd_25 = option_data_crs['0205']
                odd_aa = option_data_crs['-1-a']
                # --------------------------------------------
                flag_10 = '0100'
                flag_20 = '0200'
                flag_21 = '0201'
                flag_30 = '0300'
                flag_31 = '0301'
                flag_32 = '0302'
                flag_40 = '0400'
                flag_41 = '0401'
                flag_42 = '0402'
                flag_50 = '0500'
                flag_51 = '0501'
                flag_52 = '0502'
                flag_hh = '-1-h'

                flag_00 = '0000'
                flag_11 = '0101'
                flag_22 = '0202'
                flag_33 = '0303'
                flag_dd = '-1-d'

                flag_01 = '0001'
                flag_02 = '0002'
                flag_12 = '0102'
                flag_03 = '0003'
                flag_13 = '0103'
                flag_23 = '0203'
                flag_04 = '0004'
                flag_14 = '0104'
                flag_24 = '0204'
                flag_05 = '0005'
                flag_15 = '0105'
                flag_25 = '0205'
                flag_aa = '-1-a'

                result_crs = [(flag_10, title_10, odd_10), (flag_20, title_20, odd_20), (flag_21, title_21, odd_21),
                              (flag_30, title_30, odd_30), (flag_31, title_31, odd_31), (flag_32, title_32, odd_32),
                              (flag_40, title_40, odd_40), (flag_41, title_41, odd_41), (flag_42, title_42, odd_42),
                              (flag_50, title_50, odd_50), (flag_51, title_51, odd_51), (flag_52, title_52, odd_52),
                              (flag_hh, title_hh, odd_hh), (flag_00, title_00, odd_00), (flag_11, title_11, odd_11),
                              (flag_22, title_22, odd_22), (flag_33, title_33, odd_33), (flag_dd, title_dd, odd_dd),
                              (flag_01, title_01, odd_01), (flag_02, title_02, odd_02), (flag_12, title_12, odd_12),
                              (flag_03, title_03, odd_03), (flag_13, title_13, odd_13), (flag_23, title_23, odd_23),
                              (flag_04, title_04, odd_04), (flag_14, title_14, odd_14), (flag_24, title_24, odd_24),
                              (flag_05, title_05, odd_05), (flag_15, title_15, odd_15), (flag_25, title_25, odd_25),
                              (flag_aa, title_aa, odd_aa)]

                # option_data_hafu = data[1].get('hafu')
                # result_hafu = []
                # if option_data_hafu:
                #     title_hh = '胜胜'
                #     title_hd = '胜平'
                #     title_ha = '胜负'
                #     title_dh = '平胜'
                #     title_dd = '平平'
                #     title_da = '平负'
                #     title_ah = '负胜'
                #     title_ad = '负平'
                #     title_aa = '负负'
                #
                #     odd_hh = option_data_hafu['hh']
                #     odd_hd = option_data_hafu['hd']
                #     odd_ha = option_data_hafu['ha']
                #     odd_dh = option_data_hafu['dh']
                #     odd_dd = option_data_hafu['dd']
                #     odd_da = option_data_hafu['da']
                #     odd_ah = option_data_hafu['ah']
                #     odd_ad = option_data_hafu['ad']
                #     odd_aa = option_data_hafu['aa']
                #
                #     flag_hh = 'hh'
                #     flag_hd = 'hd'
                #     flag_ha = 'ha'
                #     flag_dh = 'dh'
                #     flag_dd = 'dd'
                #     flag_da = 'da'
                #     flag_ah = 'ah'
                #     flag_ad = 'ad'
                #     flag_aa = 'aa'
                #
                #     result_hafu = [(flag_hh, title_hh, odd_hh), (flag_hd, title_hd, odd_hd), (flag_ha, title_ha, odd_ha),
                #                    (flag_dh, title_dh, odd_dh), (flag_dd, title_dd, odd_dd), (flag_da, title_da, odd_da),
                #                    (flag_ah, title_ah, odd_ah), (flag_ad, title_ad, odd_ad), (flag_aa, title_aa, odd_aa)]

            if Quiz.objects.filter(match_flag=match_id).exists() is True:
                quiz = Quiz.objects.get(match_flag=match_id)

                rule_all = Rule.objects.filter(quiz=quiz).all()
                rule_had = rule_all.filter(type=0).first()
                rule_hhad = rule_all.filter(type=1).first()
                rule_ttg = rule_all.filter(type=3).first()
                rule_crs = rule_all.filter(type=2).first()

                change_time = get_time()
                for i in range(0, 4):
                    # 赛果
                    if i == 0:
                        update_odds(result_had, rule_had, quiz, change_time, i)
                    # 让分赛果
                    elif i == 1:
                        update_odds(result_hhad, rule_hhad, quiz, change_time, i)
                    # 比分
                    elif i == 2:
                        update_odds(result_crs, rule_crs, quiz, change_time, i)
                    # 总进球
                    elif i == 3:
                        update_odds(result_ttg, rule_ttg, quiz, change_time, i)
    else:
        print('未请求到任何数据')


class Command(BaseCommand):
    help = "爬取足球比赛"

    def handle(self, *args, **options):
        get_data_info(base_url)