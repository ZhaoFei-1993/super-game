# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import requests
import json
from .get_time import get_time
from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score, quiz_send_football_time
from quiz.models import Quiz

base_url = 'http://i.sporttery.cn/api/match_live_2/get_match_updated?callback=?'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "推送足球比赛时间"

    def add_arguments(self, parser):
        parser.add_argument('quiz_id', type=str)

    def handle(self, *args, **options):
        quiz_id = options['quiz_id']

        # try:
        #     quiz = Quiz.objects.get(pk=quiz_id)
        # except Quiz.DoesNotExist:
        #     msg = 'quiz_id = ' + str(quiz_id) + ' ,quiz_id无效'
        #     raise CommandError(msg)
        try:
            quiz_list = Quiz.objects.filter(pk=quiz_id)
            if len(quiz_list) != 0:
                quiz = quiz_list.first()
                match_flag = quiz.match_flag

                url = base_url
                str_list = ''
                time = get_time()[0:10]
                try:
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        dt = response.text
                        for i in dt[22:-3].strip('').split('},{'):
                            reslut = json.loads('{' + i + '}')
                            dt = '\"' + reslut['m_id'] + '\"' + ':' + '{' + i + '}'
                            str_list = str_list + ',' + dt
                    finall_dt = json.loads('{' + str_list[1:] + '}')

                    redis_conn = Redis()
                    q = Queue(connection=redis_conn)

                    try:
                        data_list = finall_dt[match_flag]
                    except KeyError as e:
                        if int(quiz.status) == int(Quiz.BONUS_DISTRIBUTION):
                            # 比赛已经结束和分配奖金
                            # 推送比赛时间
                            q.enqueue(quiz_send_football_time, quiz_id, 2, 0)
                            # 推送比分
                            q.enqueue(quiz_send_score, quiz_id, quiz.host_team_score, quiz.guest_team_score)
                        else:
                            # 比赛未开始
                            q.enqueue(quiz_send_football_time, quiz_id, 3, 0)
                    else:
                        host_team_score = data_list['fs_h']
                        guest_team_score = data_list['fs_a']

                        if data_list['status'] == 'Playing':
                            game_status = 0
                            if data_list['match_period'] == 'HT':
                                game_status = 1
                                # 推送比赛时间
                                q.enqueue(quiz_send_football_time, quiz_id, game_status, int(data_list['minute']) * 60)
                                # 推送比分
                                q.enqueue(quiz_send_score, quiz_id, host_team_score, guest_team_score)
                            else:
                                # 推送比赛时间
                                q.enqueue(quiz_send_football_time, quiz_id, game_status, int(data_list['minute']) * 60)
                                # 推送比分
                                q.enqueue(quiz_send_score, quiz_id, host_team_score, guest_team_score)
                        elif data_list['status'] == 'Played':
                            game_status = 2
                            # 推送比赛时间
                            q.enqueue(quiz_send_football_time, quiz_id, game_status, 0)
                            # 推送比分
                            q.enqueue(quiz_send_score, quiz_id, host_team_score, guest_team_score)
                        elif data_list['status'] == 'Fixture':
                            game_status = 3
                            # 推送比赛时间
                            q.enqueue(quiz_send_football_time, quiz_id, game_status, 0)
                            # 推送比分
                            q.enqueue(quiz_send_score, quiz_id, 0, 0)
                        print('推送成功')
                        print('-----------------------')

                except requests.ConnectionError as e:
                    print('Error', e.args)

                # with open('/tmp/debug_football_synctime', 'a+') as f:
                #     f.write('successed')
                #     f.write("\n")
                #
                # redis_conn = Redis()
                # q = Queue(connection=redis_conn)
                # # 推送比赛时间
                # q.enqueue(quiz_send_football_time, quiz_id, 0, 500)
                # # 推送比分
                # q.enqueue(quiz_send_score, quiz_id, 10, 0)
        except Exception as e:
            raise CommandError('exit ! ! !')