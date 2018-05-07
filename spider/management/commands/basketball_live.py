# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import re
import time, sched
from quiz.models import Quiz
import os
from api.settings import BASE_DIR
from .get_time import get_time


schedule = sched.scheduler(time.time, time.sleep)
live_url = 'http://info.sporttery.cn/livescore/iframe/bk_realtime.php?type=bkdata'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
cache_dir = BASE_DIR + '/spider/live_cache/basketball'


def perform_command(fun, inc):
    # 安排inc秒后再次运行自己，即周期运行
    schedule.enter(inc, 0, perform_command, (fun, inc))
    fun()


def timming_exe(fun, inc=60):
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    schedule.enter(inc, 0, perform_command, (fun, inc))
    # 持续运行，直到计划时间队列变成空为止git
    schedule.run()


def get_live_data():
    url = live_url
    time = get_time()[0:10]
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            dt = response.content.decode('utf-8')
            match_list = re.findall(r'CDATA\[(.*?)]]>', dt)
            for data in match_list:
                data_list = data.split('^')
                if len(data_list) < 4:
                    pass
                else:
                    match_id = data_list[0]

                    os.chdir(cache_dir)
                    dir = list(os.walk(cache_dir))[0][1]
                    if time not in dir:
                        os.mkdir(time)

                    os.chdir(cache_dir + '/' + time)
                    cache_name = 'cache_'+match_id
                    files = []
                    for root, sub_dirs, files in os.walk(cache_dir + '/' + time):
                        files = files
                    if cache_name not in files:
                        with open(cache_name, 'w+') as f:
                            f.write(data_list[13] + ':' + data_list[12])

                            if Quiz.objects.filter(match_flag=match_id).first() is not None:
                                quiz = Quiz.objects.filter(match_flag=match_id).first()
                                if data_list[28] == '-1':
                                    quiz.host_team_score = data_list[13]
                                    quiz.guest_team_score = data_list[12]
                                    quiz.status = quiz.ENDED
                                elif data_list[28] == '0':
                                    quiz.status = quiz.PUBLISHING
                                else:
                                    quiz.host_team_score = data_list[13]
                                    quiz.guest_team_score = data_list[12]
                                    quiz.status = quiz.REPEALED
                                quiz.save()

                                print(quiz.host_team)
                                print(quiz.guest_team)
                                print(str(quiz.host_team_score) + ':' + str(quiz.guest_team_score))
                                print('--------------------------')
                            else:
                                print('不存在该比赛')
                    else:
                        with open(cache_name, 'r') as f:
                            score = f.readline()
                        if score == data_list[13] + ':' + data_list[12]:
                            print('不需要更新')
                            print('--------------------------')
                        else:
                            with open(cache_name, 'w+') as f:
                                f.write(data_list[13] + ':' + data_list[12])

                            if Quiz.objects.filter(match_flag=match_id).first() is not None:
                                quiz = Quiz.objects.filter(match_flag=match_id).first()
                                if data_list[28] == '-1':
                                    quiz.host_team_score = data_list[13]
                                    quiz.guest_team_score = data_list[12]
                                    quiz.status = quiz.ENDED
                                elif data_list[28] == '0':
                                    quiz.status = quiz.PUBLISHING
                                else:
                                    quiz.host_team_score = data_list[13]
                                    quiz.guest_team_score = data_list[12]
                                    quiz.status = quiz.REPEALED
                                quiz.save()

                                print(quiz.host_team)
                                print(quiz.guest_team)
                                print(str(quiz.host_team_score) + ':' + str(quiz.guest_team_score))
                                print('--------------------------')
                            else:
                                print('不存在该比赛')

    except requests.ConnectionError as e:
        print('Error', e.args)


class Command(BaseCommand):
    help = "爬取篮球直播"

    def handle(self, *args, **options):
        try:
            timming_exe(get_live_data, inc=2)
        except KeyboardInterrupt as e:
            pass
