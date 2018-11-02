# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from users.models import UserMessage, CoinDetail, User
from django.db import connection


class Command(BaseCommand, BaseView):
    help = "删除"

    def handle(self, *args, **options):
        print('开始搜索robot id')
        robot_list = User.objects.filter(is_robot=1).values_list('id', flat=True)
        robot_tuple = tuple(robot_list)
        print('开始搜索robot id结束')

        print("信息表删除开始")
        sql = 'DELETE FROM users_usermessage WHERE user_id IN ' + str(robot_tuple) + ';'
        with connection.cursor() as cursor:
            cursor.execute(sql)
        print("信息表删除完成")

        print("资金记录表删除开始")
        sql = 'DELETE FROM users_coindetail WHERE user_id IN ' + str(robot_tuple) + ';'
        with connection.cursor() as cursor:
            cursor.execute(sql)
        print("资金记录表删除完成")
