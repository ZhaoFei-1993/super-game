# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import os
import requests
import json
from api.settings import BASE_DIR
import time, sched
from quiz.models import Quiz
import datetime
from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score, quiz_send_football_time
from .get_time import get_time
from utils.cache import set_cache, get_cache

schedule = sched.scheduler(time.time, time.sleep)
base_url = 'http://i.sporttery.cn/api/match_live_2/get_match_updated?callback=?'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
cache_dir = BASE_DIR + '/cache/live_cache/football'
key_quiz_live_time = 'quiz_live_time'


def perform_command(fun, inc):
    # 安排inc秒后再次运行自己，即周期运行
    schedule.enter(inc, 0, perform_command, (fun, inc))
    fun()


def timming_exe(fun, inc=60):
    # enter用来安排某事件的发生时间，从现在起第n秒开始启动
    schedule.enter(inc, 0, perform_command, (fun, inc))
    # 持续运行，直到计划时间队列变成空为止
    schedule.run()


def cache_live_time(match_id, data_list):
    quiz_live_time_dic = get_cache(key_quiz_live_time)
    if quiz_live_time_dic is None:
        set_cache(key_quiz_live_time, {match_id: data_list})
    else:
        quiz_live_time_dic[match_id] = data_list
        set_cache(key_quiz_live_time, quiz_live_time_dic)


def get_live_data():
    url = base_url
    str_list = ''
    time = get_time()[0:10]
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            dt = response.text
            for i in dt[22:-3].strip('').split('},{'):
                reslut = json.loads('{' + i + '}')
                dt = '\"' + reslut['m_id'] + '\"' + ':' + '{' + i + '}'
                str_list = str_list + ',' + dt
        finall_dt = json.loads('{' + str_list[1:] + '}')
        for key in finall_dt:
            data_list = finall_dt[key]
            if data_list['fs_h'] is not None and data_list['fs_a'] is not None:
                match_id = data_list['m_id']

                for root, sub_dirs, files in list(os.walk(BASE_DIR + '/cache/live_cache'))[0: 1]:
                    sub_dirs = sub_dirs
                if 'football' not in sub_dirs:
                    os.chdir(BASE_DIR + '/cache/live_cache')
                    os.mkdir('football')

                cache_name = 'cache_' + match_id
                os.chdir(cache_dir)
                dir = list(os.walk(cache_dir))[0][1]
                if time not in dir:
                    os.mkdir(time)

                os.chdir(cache_dir + '/' + time)
                files = []
                for root, sub_dirs, files in os.walk(cache_dir + '/' + time):
                    files = files

                redis_conn = Redis()
                q = Queue(connection=redis_conn)

                if cache_name not in files:
                    with open(cache_name, 'w+') as f:
                        f.write(data_list['fs_h'] + ':' + data_list['fs_a'] + ',')
                        f.write(data_list['status'] + ',')
                        f.write(data_list['match_period'] + ',')

                    if Quiz.objects.filter(match_flag=match_id).first() is not None:
                        quiz = Quiz.objects.filter(match_flag=match_id).first()

                        # 存入缓存供推送脚本使用
                        cache_live_time(match_id, data_list)

                        # 2H是下半场,1H是上半场,ht， fs_h是主队进球，fs_a是客队进球
                        host_team_score = data_list['fs_h']
                        guest_team_score = data_list['fs_a']

                        if data_list['status'] == 'Played':
                            game_status = 2
                            quiz.host_team_score = host_team_score
                            quiz.guest_team_score = guest_team_score
                            quiz.status = quiz.ENDED
                            quiz.gaming_time = -1
                            with open(cache_name, 'r+') as f:
                                data = f.readline()
                            if game_status != data.split(',')[3]:
                                with open(cache_name, 'w+') as f:
                                    f.write(data.split(',')[0] + ',')
                                    f.write(data.split(',')[1] + ',')
                                    f.write(data.split(',')[2] + ',')
                                    f.write(str(game_status))

                            q.enqueue(quiz_send_football_time, quiz.id, game_status, 0)

                        elif data_list['status'] == 'Fixture':
                            game_status = 3
                            quiz.status = quiz.PUBLISHING

                            q.enqueue(quiz_send_football_time, quiz.id, game_status, 0)

                        elif data_list['status'] == 'Playing':
                            gaming_time = int(data_list['minute']) * 60

                            game_status = 0

                            # 推送比赛时间
                            with open(cache_name, 'r+') as f:
                                data = f.readline()
                            if game_status != data.split(',')[3]:
                                with open(cache_name, 'w+') as f:
                                    f.write(data.split(',')[0] + ',')
                                    f.write(data.split(',')[1] + ',')
                                    f.write(data.split(',')[2] + ',')
                                    f.write(str(game_status))
                                q.enqueue(quiz_send_football_time, quiz.id, game_status, gaming_time)

                                quiz.host_team_score = host_team_score
                                quiz.guest_team_score = guest_team_score
                                quiz.status = quiz.REPEALED
                                quiz.gaming_time = gaming_time

                            if data_list['match_period'] == 'HT':
                                game_status = 1
                                quiz.status = quiz.HALF_TIME

                                # 推送比赛时间
                                with open(cache_name, 'r+') as f:
                                    data = f.readline()
                                if game_status != data.split(',')[3]:
                                    with open(cache_name, 'w+') as f:
                                        f.write(data.split(',')[0] + ',')
                                        f.write(data.split(',')[1] + ',')
                                        f.write(data.split(',')[2] + ',')
                                        f.write(str(game_status))
                                    q.enqueue(quiz_send_football_time, quiz.id, game_status,
                                              int(data_list['minute']) * 60)
                        quiz.save()

                        # 比分推送
                        q.enqueue(quiz_send_score, quiz.id, host_team_score, guest_team_score)

                        print(quiz.host_team)
                        print(quiz.guest_team)
                        print(host_team_score + ':' + guest_team_score)
                        print('--------------------------')
                    else:
                        print('不存在该比赛')
                else:
                    # 存入缓存供推送脚本使用
                    cache_live_time(match_id, data_list)

                    with open(cache_name, 'r') as f:
                        score = f.readline()

                    print(match_id)
                    if score.split(',')[0] == data_list['fs_h'] + ':' + data_list['fs_a'] \
                            and score.split(',')[1] == data_list['status'] \
                            and score.split(',')[2] == data_list['match_period']:
                        print(get_time())
                        print('不需要更新')
                        print('--------------------------')
                    else:
                        with open(cache_name, 'r+') as f:
                            data = f.readline()
                        game_status = data.split(',')[3]
                        with open(cache_name, 'w+') as f:
                            f.write(data_list['fs_h'] + ':' + data_list['fs_a'] + ',')
                            f.write(data_list['status'] + ',')
                            f.write(data_list['match_period'] + ',')
                            f.write(game_status)

                        if Quiz.objects.filter(match_flag=match_id).first() is not None:
                            quiz = Quiz.objects.filter(match_flag=match_id).first()

                            # 2H是下半场,1H是上半场,ht， fs_h是主队进球，fs_a是客队进球
                            host_team_score = data_list['fs_h']
                            guest_team_score = data_list['fs_a']

                            if data_list['status'] == 'Played':
                                game_status = 2
                                quiz.host_team_score = host_team_score
                                quiz.guest_team_score = guest_team_score
                                quiz.status = quiz.ENDED
                                quiz.gaming_time = -1
                                with open(cache_name, 'r+') as f:
                                    data = f.readline()
                                if game_status != data.split(',')[3]:
                                    with open(cache_name, 'w+') as f:
                                        f.write(data.split(',')[0] + ',')
                                        f.write(data.split(',')[1] + ',')
                                        f.write(data.split(',')[2] + ',')
                                        f.write(str(game_status))

                                q.enqueue(quiz_send_football_time, quiz.id, game_status, 0)

                            elif data_list['status'] == 'Fixture':
                                game_status = 3
                                quiz.status = quiz.PUBLISHING

                                q.enqueue(quiz_send_football_time, quiz.id, game_status, 0)

                            elif data_list['status'] == 'Playing':
                                gaming_time = int(data_list['minute']) * 60

                                game_status = 0

                                # 推送比赛时间
                                with open(cache_name, 'r+') as f:
                                    data = f.readline()
                                if game_status != data.split(',')[3]:
                                    with open(cache_name, 'w+') as f:
                                        f.write(data.split(',')[0] + ',')
                                        f.write(data.split(',')[1] + ',')
                                        f.write(data.split(',')[2] + ',')
                                        f.write(str(game_status))
                                    q.enqueue(quiz_send_football_time, quiz.id, game_status, gaming_time)

                                    quiz.host_team_score = host_team_score
                                    quiz.guest_team_score = guest_team_score
                                    quiz.status = quiz.REPEALED
                                    quiz.gaming_time = gaming_time

                                if data_list['match_period'] == 'HT':
                                    game_status = 1
                                    quiz.status = quiz.HALF_TIME

                                    # 推送比赛时间
                                    with open(cache_name, 'r+') as f:
                                        data = f.readline()
                                    if game_status != data.split(',')[3]:
                                        with open(cache_name, 'w+') as f:
                                            f.write(data.split(',')[0] + ',')
                                            f.write(data.split(',')[1] + ',')
                                            f.write(data.split(',')[2] + ',')
                                            f.write(str(game_status))
                                        q.enqueue(quiz_send_football_time, quiz.id, game_status, gaming_time)
                            quiz.save()

                            # 比分推送
                            q.enqueue(quiz_send_score, quiz.id, host_team_score, guest_team_score)

                            print(quiz.host_team)
                            print(quiz.guest_team)
                            print(host_team_score + ':' + guest_team_score)
                            print('--------------------------')
                        else:
                            print('不存在该比赛')
            else:
                print('warming')
                print('-----------------------------')
    except Exception as e:
        print('Error', e)
        raise CommandError('Error Out! ! !', datetime.datetime.now())


def live_football():
    quiz_list = Quiz.objects.filter(
        status__in=[Quiz.PUBLISHING], category__parent_id=2).order_by('begin_at')
    # print(Quiz.objects.filter(category__parent_id=2, status__in=[Quiz.REPEALED, Quiz.HALF_TIME]))
    if Quiz.objects.filter(category__parent_id=2,
                           status__in=[str(Quiz.REPEALED), str(Quiz.HALF_TIME)]).exists() or quiz_list.filter(
        begin_at__lt=datetime.datetime.now()).exists():
        get_live_data()
    else:
        # print('no match！！！')
        raise CommandError('no match！！！', datetime.datetime.now())


class Command(BaseCommand):
    help = "爬取足球直播"

    def handle(self, *args, **options):
        # try:
        #     timming_exe(get_live_data, inc=2)
        # except KeyboardInterrupt as e:
        #     pass

        live_football()
