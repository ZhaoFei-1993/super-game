# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import os
import re
import requests
import json
from bs4 import BeautifulSoup
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
from quiz.models import Category, Quiz, Rule, Option
from wc_auth.models import Admin
from .get_time import get_time


base_url = 'http://i.sporttery.cn/odds_calculator/get_odds?i_format=json&i_callback=getData&poolcode[]=mnl&poolcode[]=hdc&poolcode[]=wnm&poolcode[]=hilo'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
img_dir = BASE_DIR+'/uploads/images/spider/basketball/team_icon'
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
    for root, sub_dirs, files in os.walk(cache_dir):
        files = files
    if 'match_cache.txt' not in files:
        with open('match_cache.txt', 'a+') as f:
            pass

    datas = get_data(url)
    if len(datas['data']) != 0:
        for data in list(datas['data'].items()):
            match_id = data[1].get('id')

            with open('match_cache.txt', 'r+') as f:
                dt = f.read()
            match_id_list = dt.split(',')
            if match_id not in match_id_list:
                with open('match_cache.txt', 'a+') as f:
                    f.write(match_id + ',')

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

                # ---------------------------------------------------------------------------------------------------------
                host_team_avatar = ''
                guest_team_avatar = ''

                try:
                    img_base_url = 'http://info.sporttery.cn/basketball/info/bk_match_mnl.php?m=' + match_id
                    response_img_url = requests.get(img_base_url, headers=headers)
                    if response_img_url.status_code == 200:
                        soup = BeautifulSoup(response_img_url.text, 'lxml')
                        img_list = soup.select('div[class="aga-m"]')
                        host_team_img_url = img_list[1].img['src']
                        guest_team_img_url = img_list[0].img['src']

                        if len(re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)) > 0 and \
                                len(re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)) > 0:
                            host_team_avatar = \
                                re.findall('http://static.sporttery.(cn|com)/(.*)', host_team_img_url)[0][1].replace(
                                    '/', '_')
                            guest_team_avatar = \
                                re.findall('http://static.sporttery.(cn|com)/(.*)', guest_team_img_url)[0][
                                    1].replace('/', '_')

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

                # ---------------------------------------------------------------------------------------------------------
                if Quiz.objects.filter(match_flag=match_id).first() is None and \
                        (len(result_hilo) > 0 and len(result_wnm) > 0 and len(result_hdc) > 0 and len(result_mnl) > 0):
                    quiz = Quiz()
                    quiz.match_flag = match_id
                    quiz.category = Category.objects.filter(name=league_abbr).first()
                    quiz.host_team = host_team_abbr
                    quiz.host_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/basketball/team_icon/' + host_team_avatar
                    quiz.guest_team = guest_team_abbr
                    quiz.guest_team_avatar = MEDIA_DOMAIN_HOST + '/images/spider/basketball/team_icon/' + guest_team_avatar
                    quiz.match_name = league_abbr
                    quiz.begin_at = time
                    quiz.updated_at = created_at
                    quiz.admin = Admin.objects.filter(id=1).first()
                    quiz.created_at = created_at
                    quiz.save()

                    for i in range(4, 8):
                        # 胜负
                        if i == 4:
                            num = 0
                            rule = Rule()
                            rule.quiz = quiz
                            rule.type = i
                            rule.tips = '胜负'
                            rule.save()
                            for dt in result_mnl:
                                option = Option()
                                option.rule = rule
                                option.option = dt[1]
                                option.odds = dt[2]
                                option.flag = dt[0]
                                num = num + 1
                                option.order = num
                                option.save()
                        # 让分胜负
                        elif i == 5:
                            num = 0
                            rule = Rule()
                            rule.quiz = quiz
                            rule.type = i
                            rule.save()
                            for dt in result_hdc:
                                option = Option()
                                option.rule = rule
                                option.option = dt[1]
                                option.odds = dt[3]
                                option.flag = dt[0]
                                num = num + 1
                                option.order = num
                                option.save()

                                if dt[2][0] == '+':
                                    rule.guest_let_score = dt[2][1:]
                                else:
                                    rule.home_let_score = dt[2][1:]
                                rule.tips = '让分胜负'
                                rule.save()

                        # 大小分
                        elif i == 6:
                            num = 0
                            rule = Rule()
                            rule.quiz = quiz
                            rule.type = i
                            rule.tips = '大小分,两队总得分大于或小于预估总得分'
                            rule.save()
                            for dt in result_hilo:
                                option = Option()
                                option.rule = rule
                                option.option = dt[1].replace('+', '')
                                option.odds = dt[3]
                                option.flag = dt[0]
                                num = num + 1
                                option.order = num
                                option.save()

                                rule.estimate_score = dt[2]
                                rule.save()
                        # 胜分差
                        elif i == 7:
                            num_h = 0
                            num_a = 0
                            rule = Rule()
                            rule.quiz = quiz
                            rule.type = i
                            rule.tips = '胜分差'
                            rule.save()
                            for dt in result_wnm:
                                option = Option()
                                option.rule = rule
                                option.option = dt[1][2:]
                                option.odds = dt[2]
                                option.option_type = dt[1][0:2]
                                option.flag = dt[0]
                                if dt[1][0:2] == '主胜':
                                    num_h = num_h + 1
                                    option.order = num_h
                                elif dt[1][0:2] == '客胜':
                                    num_a = num_a + 1
                                    option.order = num_a
                                option.save()
                else:
                    print('已经存在')
                # ---------------------------------------------------------------------------------------------------------
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
                print('---------------------------------------------------------------------------------------------------')
            else:
                print('已经存在，跳过')
    else:
        print('未请求到任何数据')


class Command(BaseCommand):
    help = "爬取篮球比赛"

    def handle(self, *args, **options):
        get_data_info(base_url)
