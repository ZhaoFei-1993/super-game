# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import os
import re
import requests
import json
from bs4 import BeautifulSoup
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Category, Quiz, Rule, Option, Club, OptionOdds, QuizOddsLog
from .get_time import get_time
from django.db import transaction
import datetime
from .basketball_match import save_rule_option

base_url = 'http://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=mnl&poolcode[]=hdc&poolcode[]=wnm&poolcode[]=hilo'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def get_data(url):
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[8:-2])
            return result
    except Exception as e:
        print('Error:  ', e)
        raise CommandError('Error Out! ! !')


# 更改篮球比赛赔率放方法
def update_odds(result, quiz, rule, change_time, play_flag):
    # rule_type_name: {4: 胜负, 5: 让分胜负, 6: 大小分, 7: 胜分差}
    if rule is None:
        save_rule_option(play_flag, quiz, result)
        print('新储存 玩法：' + Rule.TYPE_CHOICE[play_flag][1])
    else:
        mark = False
        for dt in result:
            option = Option.objects.get(rule=rule, flag=dt[0])
            if play_flag == 4 or play_flag == 7:
                if float(option.odds) != float(dt[-1]):
                    mark = True
                    break
            elif play_flag == 5:
                let_score = dt[-2]
                if '-' in let_score:
                    home_let_score = let_score.replace('-', '')
                    if float(option.odds) != float(dt[-1]) or float(home_let_score) != float(rule.home_let_score):
                        mark = True
                        break
                else:
                    guest_let_score = let_score.replace('+', '')
                    if float(option.odds) != float(dt[-1]) or float(guest_let_score) != float(rule.guest_let_score):
                        mark = True
                        break
            elif play_flag == 6:
                if float(option.odds) != float(dt[-1]) or option.option != dt[1].replace('+', ''):
                    mark = True
                    break

        if mark is True:
            for dt in result:
                # 对应选项赔率相应变化
                option = Option.objects.get(rule=rule, flag=dt[0])
                if play_flag == 5:
                    let_score = dt[-2]
                    if '-' in let_score:
                        rule.home_let_score = let_score.replace('-', '')
                        rule.guest_let_score = 0
                    else:
                        rule.guest_let_score = let_score.replace('+', '')
                        rule.home_let_score = 0
                    rule.save()
                elif play_flag == 6:
                    option.option = dt[1].replace('+', '')

                option.odds = dt[-1]
                option.save()

                clubs = Club.objects.all()
                for club in clubs:
                    option_odds = OptionOdds.objects.get(club=club, quiz=quiz, option=option)
                    option_odds.odds = dt[-1]
                    option_odds.save()
            print(quiz.match_flag + ',' + quiz.host_team + 'VS' + quiz.guest_team + ' 的玩法:' + rule.tips + ',赔率已变化')
        else:
            print('无变化')


@transaction.atomic()
def get_data_info(url):
    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            match_id = data[1].get('id')

            option_data_mnl = data[1].get('mnl')
            result_mnl = []
            if option_data_mnl:
                title_a_mnl = '主负'
                title_h_mnl = '主胜'
                odd_a_mnl = option_data_mnl['a']
                odd_h_mnl = option_data_mnl['h']
                flag_a_mnl = 'a'
                flag_h_mnl = 'h'
                result_mnl = [(flag_h_mnl, title_h_mnl, odd_h_mnl), (flag_a_mnl, title_a_mnl, odd_a_mnl)]

            option_data_hdc = data[1].get('hdc')
            result_hdc = []
            if option_data_hdc:
                let_socre = option_data_hdc['fixedodds']
                title_a_hdc = '让分主负'
                title_h_hdc = '让分主胜'
                odd_a_hdc = option_data_hdc['a']
                odd_h_hdc = option_data_hdc['h']
                flag_a_hdc = 'a'
                flag_h_hdc = 'h'
                result_hdc = [(flag_h_hdc, title_h_hdc, let_socre, odd_h_hdc),
                              (flag_a_hdc, title_a_hdc, let_socre, odd_a_hdc)]

            option_data_hilo = data[1].get('hilo')
            result_hilo = []
            if option_data_hilo:
                total_socre = option_data_hilo['fixedodds']
                title_h_hilo = '总分大于' + option_data_hilo['fixedodds']
                title_l_hilo = '总分小于' + option_data_hilo['fixedodds']
                odd_h_holi = option_data_hilo['h']
                odd_l_holi = option_data_hilo['l']
                flag_h_holi = 'h'
                flag_l_holi = 'l'
                result_hilo = [(flag_h_holi, title_h_hilo, total_socre, odd_h_holi),
                               (flag_l_holi, title_l_hilo, total_socre, odd_l_holi)]

            option_data_wnm = data[1].get('wnm')
            result_wnm = []
            if option_data_wnm:
                title_w1 = '主胜' + '1-5'
                title_w2 = '主胜' + '6-10'
                title_w3 = '主胜' + '11-15'
                title_w4 = '主胜' + '16-20'
                title_w5 = '主胜' + '21-25'
                title_w6 = '主胜' + '26+'

                title_l1 = '客胜' + '1-5'
                title_l2 = '客胜' + '6-10'
                title_l3 = '客胜' + '11-15'
                title_l4 = '客胜' + '16-20'
                title_l5 = '客胜' + '21-25'
                title_l6 = '客胜' + '26+'

                odd_w1 = option_data_wnm['w1']
                odd_w2 = option_data_wnm['w2']
                odd_w3 = option_data_wnm['w3']
                odd_w4 = option_data_wnm['w4']
                odd_w5 = option_data_wnm['w5']
                odd_w6 = option_data_wnm['w6']

                odd_l1 = option_data_wnm['l1']
                odd_l2 = option_data_wnm['l2']
                odd_l3 = option_data_wnm['l3']
                odd_l4 = option_data_wnm['l4']
                odd_l5 = option_data_wnm['l5']
                odd_l6 = option_data_wnm['l6']

                flag_w1 = 'w1'
                flag_w2 = 'w2'
                flag_w3 = 'w3'
                flag_w4 = 'w4'
                flag_w5 = 'w5'
                flag_w6 = 'w6'

                flag_l1 = 'l1'
                flag_l2 = 'l2'
                flag_l3 = 'l3'
                flag_l4 = 'l4'
                flag_l5 = 'l5'
                flag_l6 = 'l6'

                result_wnm = [(flag_w1, title_w1, odd_w1), (flag_w2, title_w2, odd_w2), (flag_w3, title_w3, odd_w3),
                              (flag_w4, title_w4, odd_w4), (flag_w5, title_w5, odd_w5), (flag_w6, title_w6, odd_w6),
                              (flag_l1, title_l1, odd_l1), (flag_l2, title_l2, odd_l2), (flag_l3, title_l3, odd_l3),
                              (flag_l4, title_l4, odd_l4), (flag_l5, title_l5, odd_l5), (flag_l6, title_l6, odd_l6)]

            if Quiz.objects.filter(match_flag=match_id).exists() is True:
                quiz = Quiz.objects.get(match_flag=match_id)
                host_vs_guest = quiz.host_team + 'vs' + quiz.guest_team
                print('=======================>', host_vs_guest, quiz.match_flag, 'now is ', datetime.datetime.now())

                rule_all = Rule.objects.filter(quiz=quiz).all()
                rule_had = rule_all.filter(type=4).first()
                rule_hhad = rule_all.filter(type=5).first()
                rule_ttg = rule_all.filter(type=6).first()
                rule_crs = rule_all.filter(type=7).first()

                change_time = get_time()

                # play_flag: {4: 胜负, 5: 让分胜负, 6: 大小分, 7: 胜分差}
                result_odds_dic = {4: result_mnl, 5: result_hdc, 6: result_hilo, 7: result_wnm}
                rule_odds_dic = {4: rule_had, 5: rule_hhad, 6: rule_ttg, 7: rule_crs}
                for i in range(4, 8):
                    update_odds(result_odds_dic[i], quiz, rule_odds_dic[i], change_time, i)
    else:
        print('未请求到任何数据')


class Command(BaseCommand):
    help = "爬取篮球比赛"

    def handle(self, *args, **options):
        try:
            get_data_info(base_url)
        except Exception as e:
            raise CommandError('Error is : ', e)
