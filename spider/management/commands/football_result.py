# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import json
from quiz.models import Quiz, Rule, Option


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


def get_data_info(url, match_flag):
    datas = get_data(url + match_flag)
    if datas['status']['code'] == 0:
        if len(datas['result']['pool_rs']) > 0:
            result_had = datas['result']['pool_rs']['had']
            result_hhad = datas['result']['pool_rs']['hhad']
            result_ttg = datas['result']['pool_rs']['ttg']
            result_crs = datas['result']['pool_rs']['crs']
            # result_hafu = datas['result']['pool_rs']['hafu']

            score = result_crs['prs_name'].split(':')
            host_team_score = score[0]
            guest_team_score = score[1]

            print(score)
            print(match_flag)
            print(result_had)
            print(result_hhad)
            print(result_ttg)
            print(result_crs)

            if Quiz.objects.filter(match_flag=match_flag).first() is not None:
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

                option = Option.objects.filter(rule=rule_had).filter(flag=result_had['pool_rs']).first()
                option.is_right = 1
                option.save()

                option = Option.objects.filter(rule=rule_hhad).filter(flag=result_hhad['pool_rs']).first()
                option.is_right = 1
                option.save()

                option = Option.objects.filter(rule=rule_ttg).filter(flag=result_ttg['pool_rs']).first()
                option.is_right = 1
                option.save()

                option = Option.objects.filter(rule=rule_crs).filter(flag=result_crs['pool_rs']).first()
                option.is_right = 1
                option.save()
            else:
                print('该比赛不存在')


        else:
            print('未有开奖信息')
    else:
        print('未请求到任务数据')


class Command(BaseCommand):
    help = "爬取足球开奖结果"

    def add_arguments(self, parser):
        parser.add_argument('match_flag', type=str)

    def handle(self, *args, **options):
        get_data_info(base_url, match_flag=options['match_flag'])

