# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import requests
import json
import re
from .get_time import get_time
from rq import Queue
from redis import Redis
from quiz.consumers import quiz_send_score, quiz_send_basketball_time
from quiz.models import Quiz


live_url = 'http://info.sporttery.cn/livescore/iframe/bk_realtime.php?type=bkdata'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "推送篮球比赛时间"

    def add_arguments(self, parser):
        parser.add_argument('quiz_id', type=str)

    def handle(self, *args, **options):
        quiz_id = options['quiz_id']
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Exception as e:
            msg = 'quiz_id = ' + str(quiz_id) + ' ,quiz_id无效'
            raise CommandError(msg, e)
        match_flag = quiz.match_flag

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

                        if match_flag == match_id:
                            host_team_score = data_list[13]
                            guest_team_score = data_list[12]

                            redis_conn = Redis()
                            q = Queue(connection=redis_conn)

                            if data_list[28] == '-1':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, -1)
                            elif data_list[28] == '0':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 0)
                            elif data_list[28] == '1':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 1)
                            elif data_list[28] == '2':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 2)
                            elif data_list[28] == '50':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 50)
                            elif data_list[28] == '3':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 3)
                            elif data_list[28] == '4':
                                # 推送比赛时间
                                q.enqueue(quiz_send_basketball_time, quiz_id, 4)

                            # 推送比分
                            q.enqueue(quiz_send_score, quiz_id, host_team_score, guest_team_score)
                        else:
                            print('查找失败')
        except requests.ConnectionError as e:
            print('Error', e.args)

        # with open('/tmp/debug_basketball_synctime', 'a+') as f:
        #     f.write('successed')
        #     f.write("\n")
        #
        # redis_conn = Redis()
        # q = Queue(connection=redis_conn)
        # # 推送比赛时间
        # q.enqueue(quiz_send_basketball_time, quiz_id, 4, 500)
        # # 推送比分
        # q.enqueue(quiz_send_score, quiz_id, 100, 98)
