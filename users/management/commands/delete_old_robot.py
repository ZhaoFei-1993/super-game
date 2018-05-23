# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from users.models import User, UserCoin
from quiz.models import Record
from django.db import transaction


class Command(BaseCommand):
    """
    删除旧机器人数据
    """
    help = "删除旧机器人数据"

    @transaction.atomic()
    def handle(self, *args, **options):
        robot_users = User.objects.filter(is_robot=True, pk__lt=1364)
        self.stdout.write(self.style.SUCCESS('获取到 ' + str(len(robot_users)) + ' 个机器人'))

        user_ids = []
        for robot in robot_users:
            user_ids.append(robot.id)

        records = Record.objects.filter(user_id__in=user_ids)
        records.delete()
        self.stdout.write(self.style.SUCCESS('已删除 ' + str(len(records)) + ' 条投注记录'))

        user_coins = UserCoin.objects.filter(user_id__in=user_ids)
        user_coins.delete()
        self.stdout.write(self.style.SUCCESS('已删除 ' + str(len(user_coins)) + ' 条用户货币记录'))

        robot_users.delete()

        self.stdout.write(self.style.SUCCESS('清除成功'))
