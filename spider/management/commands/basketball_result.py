# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import re
import requests
from bs4 import BeautifulSoup
from quiz.models import Quiz, Rule, Option


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


def get_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.content
            return dt
    except requests.ConnectionError as e:
        print('Error', e.args)


def get_data_info(url, match_flag):
    datas = get_data(url+match_flag)
    soup = BeautifulSoup(datas, 'lxml')

    result_score = soup.select('span[class="k_bt"]')[0].string
    if len(re.findall('.*\((.*?:.*?)\)', result_score)) > 0 :
        host_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][1]
        guest_team_score = re.findall('.*\((.*?):(.*?)\)', result_score)[0][0]

        print(result_score)
        print(guest_team_score + ':' + host_team_score)

        result_list = soup.select('table[class="kj-table"]')
        try:
            result_mnl = result_list[0].select('span[class="win"]')[0].string.replace(' ', '')
            result_mnl_flag = result_match['result_mnl'][result_mnl]
            print(result_mnl)
            print(result_mnl_flag)
            print('----------------------------------------')
        except:
            print('未捕抓到数据')
            print(result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_hdc = result_list[1].select('span[class="win"]')[0].string
            result_hdc_flag = result_match['result_hdc'][result_hdc]
            print(result_hdc)
            print(result_hdc_flag)
            print('----------------------------------------')
        except:
            print('未捕抓到数据')
            print(result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_hilo = result_list[2].select('span[class="win"]')[0].string
            result_hilo_flag = result_match['result_hilo'][result_hilo]
            print(result_hilo)
            print(result_hilo_flag)
            print('----------------------------------------')
        except:
            print('未捕抓到数据')
            print(result_match['未捕抓到数据'])
            print('----------------------------------------')

        try:
            result_wnm = result_list[3].select('span[class="win"]')[0].string
            result_wnm_flag = result_match['result_wnm'][result_wnm]
            print(result_wnm)
            print(result_wnm_flag)
            print('----------------------------------------')
        except:
            print('未捕抓到数据')
            print(result_match['未捕抓到数据'])
            print('----------------------------------------')

    else:
        print('未有开奖信息')

# ------------------------------------------------------------------------------------------------

    if Quiz.objects.filter(match_flag=match_flag).first() is not None:
        quiz = Quiz.objects.filter(match_flag=match_flag).first()
        quiz.host_team_score = host_team_score
        quiz.guest_team_score = guest_team_score
        quiz.status = quiz.PUBLISHING_ANSWER
        quiz.save()

        rule_all = Rule.objects.filter(quiz=quiz).all()
        rule_mnl = rule_all.filter(type=4).first()
        rule_hdc = rule_all.filter(type=5).first()
        rule_hilo = rule_all.filter(type=6).first()
        rule_wnm = rule_all.filter(type=7).first()

        option = Option.objects.filter(rule=rule_mnl).filter(flag=result_mnl_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_hdc).filter(flag=result_hdc_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_hilo).filter(flag=result_hilo_flag).first()
        option.is_right = 1
        option.save()

        option = Option.objects.filter(rule=rule_wnm).filter(flag=result_wnm_flag).first()
        option.is_right = 1
        option.save()
    else:
        print('该比赛不存在')


class Command(BaseCommand):
    help = "爬取篮球开奖结果"

    def add_arguments(self, parser):
        parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        get_data_info(base_url, match_flag=options['match_flag'])
