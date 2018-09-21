# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from utils.cache import get_cache, set_cache
from guess.models import Issues
import datetime
from guess.consumers import guess_pk_detail


class Command(BaseCommand):
    help = "股指PK推送脚本"

    def handle(self, *args, **options):
        time_now = datetime.datetime.now()
        issue_time_dic = get_cache('issue_time_dic')
        if issue_time_dic is None:
            issue_last = Issues.objects.filter(open__gt=time_now).order_by('open').first()
            issue_pre = Issues.objects.filter(open__lt=time_now).order_by('-open').first()
            issue_time_dic = {
                'issue_last':
                    {'issue_id': issue_last.id, 'open_time': issue_last.open,
                     'issue': issue_last.issue, 'rest': 0, 'switch': 0,
                     },
                'issue_pre': {'issue_id': issue_pre.id, 'open_time': issue_pre.open,
                              'issue': issue_pre.issue,
                              },
            }
            set_cache('issue_time_dic', issue_time_dic)
        else:
            pre_open_time = issue_time_dic['issue_pre']['open_time']

            last_issue_id = issue_time_dic['issue_last']['issue_id']
            last_open_time = issue_time_dic['issue_last']['open_time']
            last_issue = issue_time_dic['issue_last']['issue']
            rest = issue_time_dic['issue_last']['rest']
            switch = issue_time_dic['issue_last']['switch']

            if time_now > last_open_time:
                print('推送')
                guess_pk_detail(last_issue_id)

                issue_last_obj = Issues.objects.filter(open__gt=time_now).order_by('open').first()
                issue_last = {'issue_id': issue_last_obj.id, 'open_time': issue_last_obj.open,
                              'issue': issue_last_obj.issue, 'rest': 0, 'switch': 0, }
                issue_pre = {'issue_id': last_issue_id, 'open_time': last_open_time,
                             'issue': last_issue, }
                issue_time_dic['issue_last'] = issue_last
                issue_time_dic['issue_pre'] = issue_pre

                set_cache('issue_time_dic', issue_time_dic)
            elif last_open_time.strftime('%H:%M:%S') == '13:05:00':
                if time_now > (last_open_time - datetime.timedelta(minutes=5)):
                    if rest == 0:
                        print('推送')
                        guess_pk_detail(last_issue_id)

                        issue_time_dic['issue_last']['rest'] = 1
                        set_cache('issue_time_dic', issue_time_dic)
            elif last_issue == 1:
                if time_now > (pre_open_time + datetime.timedelta(hours=1)):
                    if switch == 0:
                        print('推送')
                        guess_pk_detail(last_issue_id)

                        issue_time_dic['issue_last']['switch'] = 1
                        set_cache('issue_time_dic', issue_time_dic)
            else:
                print('暂无需变换')
