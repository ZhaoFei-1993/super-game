# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
import os
import requests
import json
from .get_time import get_time
from quiz.models import Quiz, Rule, Option, QuizOddsLog, OptionOdds
from chat.models import Club
from decimal import Decimal
import datetime
from django.db import transaction
from utils.cache import set_cache, get_cache
from time import sleep
from bs4 import BeautifulSoup
import re
from utils.functions import to_decimal
from utils.functions import get_proxies


base_url = 'https://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=had&poolcode[]=hhad&poolcode[]=ttg&poolcode[]=crs&poolcode[]=hafu'
asia_url = 'https://i.sporttery.cn/api/fb_match_info/get_asia/?f_callback=asia_tb&mid='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def get_asia_game():
    url_index = 'http://www.310win.com/buy/jingcai.aspx?typeID=105&oddstype=2'
    response = requests.get(url_index, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'lxml')
    tr_tag = soup.select('table[class="socai"]')[0].contents

    # 队名映射
    match_map = {}
    m_array = re.search('var M = new Array()(.*);', response.text)
    array_list = m_array.group().split(';')
    for dt in array_list:
        array_info = re.findall('M(.*) = (.*)', dt)
        if len(array_info) != 0:
            array_index = array_info[0][0].split('][')
            if len(array_index) == 2:
                if array_index[0][1:] not in match_map:
                    match_map.update({array_index[0][1:]: {}})

                if array_index[1] == '17]':
                    match_map[array_index[0][1:]].update({'host_team': array_info[0][1].replace('"', '')})
                elif array_index[1] == '19]':
                    match_map[array_index[0][1:]].update(
                        {'host_team_offical': array_info[0][1].replace('"', '')})
                elif array_index[1] == '20]':
                    match_map[array_index[0][1:]].update({'guest_team': array_info[0][1].replace('"', '')})
                elif array_index[1] == '22]':
                    match_map[array_index[0][1:]].update(
                        {'guest_team_offical': array_info[0][1].replace('"', '')})

    team_name_map = {}
    for key, value in match_map.items():
        team_name_map.update({value['host_team']: value['host_team_offical'],
                              value['guest_team']: value['guest_team_offical']})

    # 从比赛列表获取数据
    tr_tag.remove('\n')
    while '\n' in tr_tag:
        tr_tag.remove('\n')
    game_map = {}
    for tr_tag in tr_tag[3:]:
        if 'niDate' not in str(tr_tag):
            td_tag = tr_tag.find_all('td')

            host_team = td_tag[4].text.replace('\n', '').replace(' ', '')
            guest_team = td_tag[7].text.replace('\n', '').replace(' ', '')
            # 官方名
            host_team_offical = team_name_map[host_team]
            guest_team_offical = team_name_map[guest_team]

            handicap_url = 'http://www.310win.com/' + td_tag[11].find_all('a')[0].get('href')

            game_map.update({host_team_offical + 'vs' + guest_team_offical: handicap_url})
    return team_name_map, game_map


def get_asia_handicap(url):
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'lxml')
    tr_tag = soup.select('table[class="socai"]')[0].find_all('tr')

    # 赔率
    td_tag = tr_tag[2].find_all('td')
    host_team_odds = to_decimal(td_tag[4].text) + to_decimal(1)
    handicap = td_tag[5].text
    guest_team_odds = to_decimal(td_tag[6].text) + to_decimal(1)

    return {'host_team_odds': host_team_odds,
            'guest_team_odds': guest_team_odds,
            'handicap': handicap}


def update_asia_odds(json_dt, rule, quiz, change_time):
    handicap = json_dt['handicap']
    host_team_odds = json_dt['host_team_odds']
    guest_team_odds = json_dt['guest_team_odds']

    if rule.handicap != handicap:
        rule.handicap = handicap
        rule.save()

    if Option.objects.filter(rule=rule, order=1).exists() is not True and Option.objects.filter(rule=rule,
                                                                                                order=2) is not True:
        for i in range(1, 3):
            option = Option()
            option.rule = rule
            if i == 1:
                option.option = '主队'
                option.option_en = 'Home'
                option.odds = host_team_odds
            else:
                option.option = '客队'
                option.option_en = 'Guest'
                option.odds = guest_team_odds
            option.order = i
            option.save()
        # 记录初始赔率
        change_time = get_time()
        for option in Option.objects.filter(rule=rule):
            quiz_odds_log = QuizOddsLog()
            quiz_odds_log.quiz = quiz
            quiz_odds_log.rule = rule
            quiz_odds_log.option = option
            quiz_odds_log.option_title = option.option
            quiz_odds_log.odds = option.odds
            quiz_odds_log.change_at = change_time
            quiz_odds_log.save()

            # 生成俱乐部选项赔率表
            clubs = Club.objects.all()
            for club in clubs:
                option_odds = OptionOdds()
                option_odds.club = club
                option_odds.quiz = quiz
                option_odds.option = option
                option_odds.odds = option.odds
                option_odds.save()

    option_home = Option.objects.get(rule=rule, order=1)
    option_guest = Option.objects.get(rule=rule, order=2)
    if option_home.odds != Decimal(host_team_odds) or option_guest.odds != Decimal(guest_team_odds):

        option_home.odds = host_team_odds
        option_home.save()

        option_guest.odds = guest_team_odds
        option_guest.save()

        clubs = Club.objects.all()
        for club in clubs:
            option_odds_home = OptionOdds.objects.get(club=club, quiz=quiz, option=option_home)

            quiz_odds_log_home = QuizOddsLog()
            quiz_odds_log_home.quiz = quiz
            quiz_odds_log_home.rule = rule
            quiz_odds_log_home.option = option_home
            quiz_odds_log_home.option_title = option_home.option
            quiz_odds_log_home.odds = host_team_odds
            quiz_odds_log_home.change_at = change_time
            quiz_odds_log_home.save()
            # 对应选项赔率相应变化
            option_odds_home.odds = host_team_odds
            option_odds_home.save()

            option_odds_guest = OptionOdds.objects.get(club=club, quiz=quiz, option=option_guest)

            quiz_odds_log_guest = QuizOddsLog()
            quiz_odds_log_guest.quiz = quiz
            quiz_odds_log_guest.rule = rule
            quiz_odds_log_guest.option = option_guest
            quiz_odds_log_guest.option_title = option_guest.option
            quiz_odds_log_guest.odds = guest_team_odds
            quiz_odds_log_guest.change_at = change_time
            quiz_odds_log_guest.save()
            # 对应选项赔率相应变化
            option_odds_guest.odds = guest_team_odds
            option_odds_guest.save()

        option_home.save()
        option_guest.save()

        print(quiz.match_flag + ',' + quiz.host_team + 'VS' + quiz.guest_team + ' 的玩法:' + rule.tips + ',赔率已变化')
        print('=================================================')
    else:
        print('亚盘无变化')


def update_odds(result, rule, quiz, change_time, flag):
    mark = False
    for dt in result:
        option = Option.objects.filter(rule=rule, flag=dt[0]).first()
        if flag == 1:
            guest_let_score = 0
            home_let_score = 0
            if dt[1][0] == '+':
                guest_let_score = dt[1][1]
            else:
                home_let_score = dt[1][1]

            if float(option.odds) != float(dt[2]) or float(guest_let_score) != float(rule.guest_let_score) or float(
                    home_let_score) != float(rule.home_let_score):
                mark = True
                break
        else:
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

                rule.home_let_score = float(home_let_score)
                rule.guest_let_score = float(guest_let_score)
                rule.save()

                clubs = Club.objects.all()
                for club in clubs:
                    option_odds = OptionOdds.objects.get(club=club, quiz=quiz, option=option)
                    option_odds.odds = dt[2]
                    option_odds.save()

                option.save()
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

                clubs = Club.objects.all()
                for club in clubs:
                    option_odds = OptionOdds.objects.get(club=club, quiz=quiz, option=option)
                    option_odds.odds = dt[2]
                    option_odds.save()
                option.save()
        print(quiz.match_flag + ',' + quiz.host_team + 'VS' + quiz.guest_team + ' 的玩法:' + rule.tips + ',赔率已变化')
        print('=================================================')
    else:
        print('无变化', datetime.datetime.now())


def get_data(url):
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[8:-2])
            return result
    except Exception as e:
        print('Error', e)
        raise CommandError('Error', e)


@transaction.atomic()
def get_data_info(url):
    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            sleep(5)
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
                change_time = get_time()
                quiz = Quiz.objects.get(match_flag=match_id)
                host_vs_guest = quiz.host_team + 'vs' + quiz.guest_team
                print('=======================>', host_vs_guest, quiz.match_flag, 'now is ', datetime.datetime.now())

                rule_all = Rule.objects.filter(quiz=quiz).all()
                rule_had = rule_all.filter(type=0).first()
                rule_hhad = rule_all.filter(type=1).first()
                rule_ttg = rule_all.filter(type=3).first()
                rule_crs = rule_all.filter(type=2).first()

                # 亚盘玩法
                # try:
                team_name_map, game_map = get_asia_game()
                if (quiz.host_team + 'vs' + quiz.guest_team) in game_map:
                    if rule_all.filter(type=8).exists():
                        rule_asia = rule_all.filter(type=8).first()
                    else:
                        rule_asia = Rule()
                        rule_asia.quiz = quiz
                        rule_asia.type = str(Rule.AISA_RESULTS)
                        rule_asia.type_en = str(Rule.AISA_RESULTS)
                        rule_asia.tips = '亚盘'
                        rule_asia.tips_en = 'Asian Handicap'
                        rule_asia.handicap = ''
                        rule_asia.save()
                    json_dt = get_asia_handicap(game_map[quiz.host_team + 'vs' + quiz.guest_team])
                    update_asia_odds(json_dt, rule_asia, quiz, change_time)
                # except Exception as e:
                #     print('亚盘 Error is : ', e)

                # # 亚盘玩法
                # try:
                #     proxies = get_proxies()
                #     response_asia = requests.get(asia_url + match_id, headers=headers, proxies=proxies, timeout=15)
                #     dt = response_asia.text.encode("utf-8").decode('unicode_escape')
                #     json_dt = eval(dt[8:-2])
                # except Exception as e:
                #     # raise CommandError('亚盘 Error is : ', e)
                #     print('亚盘 Error is : ', e)
                # else:
                #     if json_dt['status']['code'] == 0:
                #         if rule_all.filter(type=8).exists():
                #             rule_asia = rule_all.filter(type=8).first()
                #         else:
                #             rule_asia = Rule()
                #             rule_asia.quiz = quiz
                #             rule_asia.type = str(Rule.AISA_RESULTS)
                #             rule_asia.type_en = str(Rule.AISA_RESULTS)
                #             rule_asia.tips = '亚盘'
                #             rule_asia.tips_en = 'Asian Handicap'
                #             rule_asia.handicap = json_dt['result']['data'][0]['o3'].replace('\\', '')
                #             rule_asia.save()
                #         update_asia_odds(json_dt, rule_asia, quiz, change_time)

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
    help = "刷新足球赔率"

    def handle(self, *args, **options):
        # 缓存锁 football_odds_lock 锁为1时锁住不执行，锁为0时则可执行
        key = 'football_odds_lock'
        value = get_cache(key)
        if value is None:
            set_cache(key, 0)
            value = get_cache(key)

        if value == 1:
            raise CommandError('lock out, exit！! !')
        else:
            print('通过缓存锁，可以运行')
            set_cache(key, 1)
            try:
                get_data_info(base_url)
            except Exception as e:
                set_cache(key, 0)
                raise CommandError('Error is : ', e)
            set_cache(key, 0)
