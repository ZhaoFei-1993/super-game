# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import requests
import re
import time, sched
from quiz.models import Quiz
import os
import datetime
from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score, quiz_send_basketball_time
from api.settings import BASE_DIR
from .get_time import get_time


schedule = sched.scheduler(time.time, time.sleep)
live_url = 'http://info.sporttery.cn/livescore/iframe/bk_realtime.php?type=bkdata'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
cache_dir = BASE_DIR + '/cache/live_cache/basketball'


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
                    host_team_score = data_list[13]
                    guest_team_score = data_list[12]

                    redis_conn = Redis()
                    q = Queue(connection=redis_conn)

                    if cache_name not in files:
                        with open(cache_name, 'w+') as f:
                            f.write(data_list[13] + ':' + data_list[12] + ',')
                            f.write(data_list[28])

                            if Quiz.objects.filter(match_flag=match_id).first() is not None:
                                quiz = Quiz.objects.filter(match_flag=match_id).first()
                                if data_list[28] == '-1':
                                    quiz.host_team_score = host_team_score
                                    quiz.guest_team_score = guest_team_score
                                    quiz.status = quiz.ENDED
                                elif data_list[28] == '0':
                                    quiz.status = quiz.PUBLISHING
                                else:
                                    quiz.host_team_score = data_list[13]
                                    quiz.guest_team_score = data_list[12]
                                    quiz.status = quiz.REPEALED
                                quiz.save()

                                # 比分推送
                                redis_conn = Redis()
                                q = Queue(connection=redis_conn)
                                q.enqueue(quiz_send_score, quiz.id, host_team_score, guest_team_score)

                                print(quiz.host_team)
                                print(quiz.guest_team)
                                print(str(quiz.host_team_score) + ':' + str(quiz.guest_team_score))
                                print('--------------------------')
                            else:
                                print('不存在该比赛')
                    else:
                        with open(cache_name, 'r') as f:
                            score = f.readline()
                        if score.split(',')[0] == data_list[13] + ':' + data_list[12] and \
                                score.split(',')[1] == data_list[28]:
                            print('不需要更新')
                            print('--------------------------')
                        else:
                            with open(cache_name, 'w+') as f:
                                f.write(data_list[13] + ':' + data_list[12] + ',')
                                f.write(data_list[28])

                            if Quiz.objects.filter(match_flag=match_id).first() is not None:
                                quiz = Quiz.objects.filter(match_flag=match_id).first()
                                if data_list[28] == '-1':
                                    quiz.status = quiz.ENDED
                                    quiz.gaming_time = -1
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, -1)
                                elif data_list[28] == '0':
                                    quiz.status = quiz.PUBLISHING
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 0)
                                elif data_list[28] == '1':
                                    quiz.status = quiz.PUBLISHING
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 1)
                                elif data_list[28] == '2':
                                    quiz.status = quiz.PUBLISHING
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 2)
                                elif data_list[28] == '50':
                                    quiz.status = quiz.HALF_TIME
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 50)
                                elif data_list[28] == '3':
                                    quiz.status = quiz.PUBLISHING
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 3)
                                elif data_list[28] == '4':
                                    quiz.status = quiz.PUBLISHING
                                    # 推送比赛时间
                                    q.enqueue(quiz_send_basketball_time, quiz.id, 4)
                                # 1,2,3,4:第一二三四节，50中场休息
                                quiz.host_team_score = host_team_score
                                quiz.guest_team_score = guest_team_score
                                quiz.save()

                                # 比分推送
                                q.enqueue(quiz_send_score, quiz.id, host_team_score, guest_team_score)

                                print(quiz.host_team)
                                print(quiz.guest_team)
                                print(str(quiz.host_team_score) + ':' + str(quiz.guest_team_score))
                                print('--------------------------')
                            else:
                                print('不存在该比赛')

    except requests.ConnectionError as e:
        print('Error', e.args)


def live_basketball():
    quiz_list = Quiz.objects.filter(
        status__in=[Quiz.PUBLISHING], category__parent_id=1).order_by('begin_at')
    if Quiz.objects.filter(category__parent_id=1,
                           status__in=[Quiz.REPEALED, Quiz.HALF_TIME]).exists() or quiz_list.filter(
            begin_at__lt=datetime.datetime.now()).exists():
        get_live_data()
    else:
        print('no match！！！')
        raise CommandError('no match！！！')


class Command(BaseCommand):
    help = "爬取篮球直播"

    def handle(self, *args, **options):
        # try:
        #     timming_exe(get_live_data, inc=2)
        # except KeyboardInterrupt as e:
        #     pass

        live_basketball()
