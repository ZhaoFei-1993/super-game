# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import re
import requests
import json
from bs4 import BeautifulSoup
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Category, Quiz, Rule, Option, Club, OptionOdds, QuizOddsLog
from wc_auth.models import Admin
from .get_time import get_time
from utils.functions import request_with_proxy
from django.db import transaction


base_url = 'http://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=mnl&poolcode[]=hdc&poolcode[]=wnm&poolcode[]=hilo'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR+'/uploads/images/spider/basketball/team_icon'
cache_dir = BASE_DIR + '/cache'


def get_data(url):
    try:
        response = request_with_proxy(url, headers=headers, timeout=15)
        if response.status_code == 200:
            dt = response.text.encode("utf-8").decode('unicode_escape')
            result = json.loads(dt[8:-2])
            return result
    except Exception as e:
        print('Error', e)


def save_rule_option(rule_type, quiz, result):
    # 胜负
    if rule_type == 4 and len(result) > 0:
        odds_pool_mnl = []
        num = 0
        rule = Rule()
        rule.quiz = quiz
        rule.type = rule_type
        rule.type_en = rule_type
        rule.tips = '胜负'
        rule.tips_en = ' Winner'
        rule.save()
        for dt in result:
            option = Option()
            option.rule = rule
            option.option = dt[1]
            if dt[1] == '主负':
                option.option_en = 'Away'
            elif dt[1] == '主胜':
                option.option_en = 'Home'

            option.odds = dt[2]
            odds_pool_mnl.append(float(dt[2]))
            option.flag = dt[0]
            num = num + 1
            option.order = num
            option.save()
        rule.max_odd = max(odds_pool_mnl)
        rule.min_odd = min(odds_pool_mnl)
        rule.save()
        odds_pool_mnl.clear()

    # 让分胜负
    elif rule_type == 5 and len(result) > 0:
        odds_pool_hdc = []
        num = 0
        rule = Rule()
        rule.quiz = quiz
        rule.type = rule_type
        rule.type_en = rule_type
        rule.save()
        for dt in result:
            option = Option()
            option.rule = rule
            option.option = dt[1]
            if dt[1] == '让分主负':
                option.option_en = 'Away'
            elif dt[1] == '让分主胜':
                option.option_en = 'Home'

            option.odds = dt[3]
            odds_pool_hdc.append(float(dt[3]))
            option.flag = dt[0]
            num = num + 1
            option.order = num
            option.save()

            if dt[2][0] == '+':
                rule.guest_let_score = dt[2][1:]
            else:
                rule.home_let_score = dt[2][1:]
            rule.tips = '让分胜负'
            rule.tips_en = 'Handicap Results'
            rule.save()
        rule.max_odd = max(odds_pool_hdc)
        rule.min_odd = min(odds_pool_hdc)
        rule.save()
        odds_pool_hdc.clear()

    # 大小分
    elif rule_type == 6 and len(result) > 0:
        odds_pool_hilo = []
        num = 0
        rule = Rule()
        rule.quiz = quiz
        rule.type = rule_type
        rule.type_en = rule_type
        rule.tips = '大小分'
        rule.tips_en = 'Compare the total score'
        rule.save()
        for dt in result:
            option = Option()
            option.rule = rule
            option.option = dt[1].replace('+', '')
            if '总分大于' in dt[1].replace('+', ''):
                option.option_en = 'More than ' + dt[2].replace('+', '')
            else:
                option.option_en = 'Less than ' + dt[2].replace('+', '')
            odds_pool_hilo.append(float(dt[3]))
            option.flag = dt[0]
            num = num + 1
            option.order = num
            option.odds = dt[-1]
            option.save()

            rule.estimate_score = dt[2]
            rule.save()
        rule.max_odd = max(odds_pool_hilo)
        rule.min_odd = min(odds_pool_hilo)
        rule.save()
        odds_pool_hilo.clear()

    # 胜分差
    elif rule_type == 7 and len(result) > 0:
        odds_pool_wnm = []
        num_h = 0
        num_a = 0
        rule = Rule()
        rule.quiz = quiz
        rule.type = rule_type
        rule.type_en = rule_type
        rule.tips = '胜分差'
        rule.tips_en = 'Wins the gap'
        rule.save()
        for dt in result:
            option = Option()
            option.rule = rule
            option.option = dt[1][2:]
            option.option_en = dt[1][2:]
            option.odds = dt[2]
            odds_pool_wnm.append(float(dt[2]))
            option.option_type = dt[1][0:2]
            option.flag = dt[0]
            if dt[1][0:2] == '主胜':
                num_h = num_h + 1
                option.order = num_h
            elif dt[1][0:2] == '客胜':
                num_a = num_a + 1
                option.order = num_a
            option.save()
        rule.max_odd = max(odds_pool_wnm)
        rule.min_odd = min(odds_pool_wnm)
        rule.save()
        odds_pool_wnm.clear()

    # 记录初始赔率
    change_time = get_time()
    for rule in Rule.objects.filter(quiz=quiz):
        for option in Option.objects.filter(rule=rule):
            if OptionOdds.objects.filter(option_id=option.id).exists() is not True:
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


@transaction.atomic()
def get_data_info(url):
    # 记录成功入库的比赛的match_flag
    cache_flag_list = []

    os.chdir(cache_dir)
    files = []
    for root, sub_dirs, files in list(os.walk(cache_dir))[0:1]:
        files = files
    if 'match_cache.txt' not in files:
        with open('match_cache.txt', 'a+') as f:
            pass
    with open('match_cache.txt', 'r+') as f:
        dt = f.read()
    match_id_list = dt.split(',')

    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            match_id = data[1].get('id')
            # 判断比赛是否已经获取了
            if match_id in match_id_list:
                print(match_id, ' 已经存在')
                continue
            league = data[1].get('l_cn')
            league_abbr = data[1].get('l_cn_abbr')
            guest_team = data[1].get('a_cn')
            guest_team_id = data[1].get('a_id_dc')
            guest_team_abbr = data[1].get('a_cn_abbr')

            host_team = data[1].get('h_cn')
            host_team_id = data[1].get('h_id_dc')
            host_team_abbr = data[1].get('h_cn_abbr')
            host_team_order = data[1].get('h_order')
            guest_team_order = data[1].get('a_order')
            if len(host_team_order) == 0 and len(guest_team_order) == 0:
                host_team_order = ' '
                guest_team_order = ' '
            else:
                pass

            host_team_url = 'http://i.sporttery.cn/api/bk_match_info/get_team_data?tid=' + host_team_id
            guest_team_url = 'http://i.sporttery.cn/api/bk_match_info/get_team_data?tid=' + guest_team_id
            try:
                response_host_team = request_with_proxy(host_team_url, headers=headers)
                response_guest_team = request_with_proxy(guest_team_url, headers=headers)
                if response_host_team is None or response_guest_team is None:
                    continue

                host_team_dt = response_host_team.json()
                guest_team_dt = response_guest_team.json()
            except Exception as e:
                print(e)
                continue

            if host_team_dt['status']['code'] == 0:
                host_team_en = host_team_dt['result']['official_name']
            else:
                host_team_en = ''
            if guest_team_dt['status']['code'] == 0:
                guest_team_en = guest_team_dt['result']['official_name']
            else:
                guest_team_en = ''

            time = data[1].get('date') + ' ' + data[1].get('time')
            created_at = get_time()

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
                result_hdc = [(flag_h_hdc, title_h_hdc, let_socre, odd_h_hdc), (flag_a_hdc, title_a_hdc, let_socre, odd_a_hdc)]

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
                result_hilo = [(flag_h_holi, title_h_hilo, total_socre, odd_h_holi), (flag_l_holi, title_l_hilo, total_socre, odd_l_holi)]

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

            # ------------------------------------------------------------------------------------------------------

            host_team_avatar = '篮球主队.png'
            guest_team_avatar = '篮球客队.png'
            os.chdir(img_dir)
            if os.path.exists(host_team_abbr + '.png'):
                host_team_avatar = host_team_abbr + '.png'
            elif os.path.exists(host_team + '.png'):
                host_team_avatar = host_team + '.png'

            if os.path.exists(guest_team_abbr + '.png'):
                guest_team_avatar = guest_team_abbr + '.png'
            elif os.path.exists(guest_team + '.png'):
                host_team_avatar = guest_team + '.png'

            # try:
            #     img_base_url = 'http://info.sporttery.cn/basketball/info/bk_match_mnl.php?m=' + match_id
            #     response_img_url = requests.get(img_base_url, headers=headers)
            #     if response_img_url.status_code == 200:
            #         soup = BeautifulSoup(response_img_url.text, 'lxml')
            #         img_list = soup.select('div[class="aga-m"]')
            #         host_team_img_url = img_list[1].img['src']
            #         guest_team_img_url = img_list[0].img['src']
            #
            #         if len(re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)) > 0 and \
            #                 len(re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)) > 0:
            #             host_team_avatar = \
            #                 re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)[0][1].replace(
            #                     '/', '_')
            #             guest_team_avatar = \
            #                 re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)[0][
            #                     1].replace('/', '_')
            #
            #             files = []
            #             source_dir = img_dir
            #             for root, sub_dirs, files in os.walk(source_dir):
            #                 files = files
            #
            #             if host_team_avatar not in files:
            #                 response_img = requests.get(host_team_img_url)
            #                 img = response_img.content
            #                 os.chdir(img_dir)
            #                 with open(host_team_avatar, 'wb') as f:
            #                     f.write(img)
            #             else:
            #                 print('图片已经存在')
            #
            #             if guest_team_avatar not in files:
            #                 response_img = requests.get(guest_team_img_url)
            #                 img = response_img.content
            #                 os.chdir(img_dir)
            #                 with open(guest_team_avatar, 'wb') as f:
            #                     f.write(img)
            #             else:
            #                 print('图片已经存在')
            #
            # except requests.ConnectionError as e:
            #     print('Error', e.args)

        # ------------------------------------------------------------------------------------------------------
            if Quiz.objects.filter(match_flag=match_id).first() is None:
                quiz = Quiz()
                quiz.match_flag = match_id

                if Category.objects.filter(name=league_abbr).first() is None:
                    category = Category()
                    category.name = league_abbr
                    category.admin = Admin.objects.filter(id=1).first()
                    category.parent = Category.objects.filter(id=2).first()
                    category.save()
                quiz.category = Category.objects.filter(name=league_abbr).first()

                # if quiz.category.name != '美职篮':
                #     return

                quiz.host_team = host_team_abbr
                quiz.host_team_fullname = host_team
                quiz.host_team_en = host_team_en
                quiz.host_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/basketball/team_icon/' + host_team_avatar
                quiz.guest_team = guest_team_abbr
                quiz.guest_team_fullname = guest_team
                quiz.guest_team_en = guest_team_en
                quiz.guest_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/basketball/team_icon/' + guest_team_avatar
                quiz.match_name = league_abbr
                quiz.begin_at = time
                quiz.updated_at = created_at
                quiz.admin = Admin.objects.filter(id=1).first()
                quiz.created_at = created_at
                quiz.save()

                for i in range(4, 8):
                    # 胜负
                    if i == 4 and len(result_mnl) > 0:
                        save_rule_option(i, quiz, result_mnl)

                    # 让分胜负
                    elif i == 5 and len(result_hdc) > 0:
                        save_rule_option(i, quiz, result_hdc)

                    # 大小分
                    elif i == 6 and len(result_hilo) > 0:
                        save_rule_option(i, quiz, result_hilo)

                    # 胜分差
                    elif i == 7 and len(result_wnm) > 0:
                        save_rule_option(i, quiz, result_wnm)

                cache_flag_list.append(match_id)
            else:
                print('已经存在')
            # ------------------------------------------------------------------------------------------------------
            print(match_id)
            print(league)
            print(league_abbr)
            print(guest_team)
            print(host_team)
            print(time)
            print(created_at)
            print(result_mnl)
            print(result_hdc)
            print(result_wnm)
            print(result_hilo)
            print('-----------------------------------------------------------------------------------------------')

        # 写入文件不再重复获取比赛
        if len(cache_flag_list) > 0:
            os.chdir(cache_dir)
            with open('match_cache.txt', 'a+') as f:
                f.writelines(','.join(cache_flag_list) + ',')
    else:
        print('未请求到任何数据')


class Command(BaseCommand):
    help = "爬取篮球比赛"

    def handle(self, *args, **options):
        get_data_info(base_url)
