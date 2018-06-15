# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, Robot, LoginRecord
import datetime


class Command(BaseCommand):
    help = "处理可疑用户"

    def handle(self, *args, **options):
        # 处理空的longin type
        for longin_record in LoginRecord.objects.filter(login_type=''):
            longin_record.login_type = 'HTML5'
            longin_record.save()

        i = 0
        j = 0
        # 处理Robot表
        for user in User.objects.filter(is_robot=False, is_block=False,
                                        created_at__gte=datetime.datetime(2018, 6, 14, 0, 0), source=str(User.HTML5)):
            robot = Robot()
            robot.user = user

            if LoginRecord.objects.filter(user=user).exists() is not True:
                create_at = User.objects.get(pk=user.pk).created_at
                robot.created_at = create_at
                robot.status = True

                i += 1
                print('====================>>>>  i=', i)
            else:
                create_at = User.objects.get(pk=user.pk).created_at
                log_at = LoginRecord.objects.filter(user=user).order_by('login_time').first().login_time
                if log_at - create_at > datetime.timedelta(minutes=20):
                    robot.created_at = create_at
                    robot.log_at = log_at
                    robot.status = True

                    j += 1
                    print('====================>>>>  j=', j)
                else:
                    robot.created_at = create_at
                    robot.log_at = log_at
            robot.save()
