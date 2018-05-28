# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import re
import requests
import json
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Quiz, Rule, Option, Quiz_Odds_Log, OptionOdds, Club
from quiz.models import Category
from wc_auth.models import Admin
from .get_time import get_time

base_url = 'http://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=had&poolcode[]=hhad&poolcode[]=ttg&poolcode[]=crs&poolcode[]=hafu'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR + '/uploads/images/spider/football/team_icon'
cache_dir = BASE_DIR + '/cache'


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
    os.chdir(cache_dir)
    files = []
    for root, sub_dirs, files in list(os.walk(cache_dir))[0:1]:
        files = files
    if 'match_cache.txt' not in files:
        with open('match_cache.txt', 'a+') as f:
            pass

    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            match_id = data[1].get('id')
            league = data[1].get('l_cn')
            league_abbr = data[1].get('l_cn_abbr')
            guest_team = data[1].get('a_cn')
            guest_team_abbr = data[1].get('a_cn_abbr')
            host_team = data[1].get('h_cn')
            host_team_abbr = data[1].get('h_cn_abbr')
            host_team_order = data[1].get('h_order')
            guest_team_order = data[1].get('a_order')
            if len(host_team_order) == 0 and len(guest_team_order) == 0:
                host_team_order = ' '
                guest_team_order = ' '
            else:
                pass
            time = data[1].get('date') + ' ' + data[1].get('time')
            created_at = get_time()

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

                # ------------------------------------------------------------------------------------------------------
                os.chdir(cache_dir)
                with open('match_cache.txt', 'r+') as f:
                    dt = f.read()
                match_id_list = dt.split(',')
                if match_id not in match_id_list and \
                        (len(result_crs) > 0 and len(result_ttg) > 0 and len(result_hhad) > 0 and len(result_had) > 0):
                    with open('match_cache.txt', 'a+') as f:
                        f.write(match_id + ',')

                    host_team_avatar = ''
                    guest_team_avatar = ''

                    try:
                        img_base_url = 'http://i.sporttery.cn/api/fb_match_info/get_match_info?mid=' + match_id + '&f_callback=getMatchInfo'
                        response_img_url = requests.get(img_base_url, headers=headers)
                        if response_img_url.status_code == 200:
                            dt = response_img_url.text.encode("utf-8").decode('unicode_escape')
                            result = json.loads(dt[13:-2])
                            host_team_img_url = result['result']['h_pic']
                            guest_team_img_url = result['result']['a_pic']

                            if len(re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)) > 0 and \
                                    len(re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)) > 0:
                                host_team_avatar = \
                                    re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)[0][
                                        1].replace(
                                        '/',
                                        '_')
                                guest_team_avatar = \
                                    re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)[0][
                                        1].replace(
                                        '/', '_')

                                files = []
                                source_dir = img_dir
                                for root, sub_dirs, files in os.walk(source_dir):
                                    files = files

                                if host_team_avatar not in files:
                                    response_img = requests.get(host_team_img_url)
                                    img = response_img.content
                                    os.chdir(img_dir)
                                    with open(host_team_avatar, 'wb') as f:
                                        f.write(img)
                                else:
                                    print('图片已经存在')

                                if guest_team_avatar not in files:
                                    response_img = requests.get(guest_team_img_url)
                                    img = response_img.content
                                    os.chdir(img_dir)
                                    with open(guest_team_avatar, 'wb') as f:
                                        f.write(img)
                                else:
                                    print('图片已经存在')

                    except requests.ConnectionError as e:
                        print('Error', e.args)
                    # ------------------------------------------------------------------------------------------------------
                    if Quiz.objects.filter(match_flag=match_id).exists() is not True:
                        quiz = Quiz()
                        quiz.match_flag = match_id

                        if Category.objects.filter(name=league_abbr).first() is None:
                            category = Category()
                            category.name = league_abbr
                            category.admin = Admin.objects.filter(id=1).first()
                            category.parent = Category.objects.filter(id=2).first()
                            category.save()
                        quiz.category = Category.objects.filter(name=league_abbr).first()

                        quiz.host_team = host_team_abbr
                        quiz.host_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/football/team_icon/' + host_team_avatar
                        quiz.guest_team = guest_team_abbr
                        quiz.guest_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/football/team_icon/' + guest_team_avatar
                        quiz.match_name = league_abbr
                        quiz.begin_at = time
                        quiz.updated_at = created_at
                        quiz.admin = Admin.objects.filter(id=1).first()
                        if Quiz.objects.filter(host_team=host_team_abbr, guest_team=guest_team_abbr, begin_at=time).exists():
                            quiz.status = Quiz.REPEAT_GAME
                        else:
                            pass
                        quiz.save()
                        for i in range(0, 4):
                            # 赛果
                            if i == 0:
                                odds_pool_had = []
                                num = 0
                                rule = Rule()
                                rule.quiz = quiz
                                rule.type = i
                                rule.tips = '赛果'
                                rule.save()
                                for dt in result_had:
                                    option = Option()
                                    option.rule = rule
                                    option.option = dt[1]
                                    option.odds = dt[2]
                                    odds_pool_had.append(float(dt[2]))
                                    option.flag = dt[0]
                                    num = num + 1
                                    option.order = num
                                    option.save()
                                rule.max_odd = max(odds_pool_had)
                                rule.min_odd = min(odds_pool_had)
                                rule.save()
                                odds_pool_had.clear()

                            # 让分赛果
                            elif i == 1:
                                odds_pool_hhad = []
                                num = 0
                                rule = Rule()
                                rule.quiz = quiz
                                rule.type = i
                                rule.save()
                                for dt in result_hhad:
                                    option = Option()
                                    option.rule = rule
                                    option.option = dt[1][2:]
                                    option.odds = dt[2]
                                    odds_pool_hhad.append(float(dt[2]))
                                    option.flag = dt[0]
                                    num = num + 1
                                    option.order = num
                                    option.save()

                                    if dt[1][0] == '+':
                                        rule.guest_let_score = dt[1][1]
                                    else:
                                        rule.home_let_score = dt[1][1]
                                    rule.tips = '让分赛果'
                                    rule.save()
                                rule.max_odd = max(odds_pool_hhad)
                                rule.min_odd = min(odds_pool_hhad)
                                rule.save()
                                odds_pool_hhad.clear()

                            # 比分
                            elif i == 2:
                                odds_pool_crs = []
                                num_h = 0
                                num_d = 0
                                num_a = 0
                                rule = Rule()
                                rule.quiz = quiz
                                rule.type = i
                                rule.tips = '比分'
                                rule.save()
                                for dt in result_crs:
                                    option = Option()
                                    option.rule = rule
                                    option.option = dt[1]
                                    option.odds = dt[2]
                                    odds_pool_crs.append(float(dt[2]))
                                    if dt[1] == '胜其他' or dt[1] == '平其他' or dt[1] == '负其他':
                                        if dt[1] == '胜其他':
                                            option.option_type = '胜'
                                            num_h = num_h + 1
                                            option.order = num_h
                                        elif dt[1] == '平其他':
                                            option.option_type = '平'
                                            num_d = num_d + 1
                                            option.order = num_d
                                        elif dt[1] == '负其他':
                                            option.option_type = '负'
                                            num_a = num_a + 1
                                            option.order = num_a
                                    else:
                                        score = dt[1].split(':')
                                        if score[0] > score[1]:
                                            option.option_type = '胜'
                                            num_h = num_h + 1
                                            option.order = num_h
                                        elif score[0] == score[1]:
                                            option.option_type = '平'
                                            num_d = num_d + 1
                                            option.order = num_d
                                        elif score[0] < score[1]:
                                            option.option_type = '负'
                                            num_a = num_a + 1
                                            option.order = num_a
                                    option.flag = dt[0]
                                    option.save()
                                rule.max_odd = max(odds_pool_crs)
                                rule.min_odd = min(odds_pool_crs)
                                rule.save()
                                odds_pool_crs.clear()

                            # 总进球
                            elif i == 3:
                                odds_pool_ttg = []
                                num = 0
                                rule = Rule()
                                rule.quiz = quiz
                                rule.type = i
                                rule.tips = '总进球'
                                rule.save()
                                for dt in result_ttg:
                                    option = Option()
                                    option.rule = rule
                                    option.option = dt[1]
                                    option.odds = dt[2]
                                    odds_pool_ttg.append(float(dt[2]))
                                    option.flag = dt[0]
                                    num = num + 1
                                    option.order = num
                                    option.save()
                                rule.max_odd = max(odds_pool_ttg)
                                rule.min_odd = min(odds_pool_ttg)
                                rule.save()
                                odds_pool_ttg.clear()

                        # 记录初始赔率
                        quiz = Quiz.objects.get(match_flag=match_id)
                        for rule in Rule.objects.filter(quiz=quiz):
                            for option in Option.objects.filter(rule=rule):
                                quiz_odds_log = Quiz_Odds_Log()
                                quiz_odds_log.quiz = quiz
                                quiz_odds_log.rule = rule
                                quiz_odds_log.option = option.option
                                quiz_odds_log.odds = option.odds
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
                    else:
                        print('已经存在')
                    # --------------------------------------------------------------------------------------------------
                    print(match_id)
                    print(league)
                    print(league_abbr)
                    print(guest_team)
                    print(host_team)
                    print(time)
                    print(created_at)
                    print(result_had)
                    print(result_hhad)
                    print(result_ttg)
                    print(result_crs)
                    # print(result_hafu)
                    print('-------------------------------------------------------------------------------------------')
                else:
                    print('已经存在，跳过或者还没开售')
    else:
        print('未请求到任何数据')


class Command(BaseCommand):
    help = "爬取足球比赛"

    def handle(self, *args, **options):
        get_data_info(base_url)
