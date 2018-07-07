# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from users.models import FinanceUserModel
from django.db import transaction


class Command(BaseCommand):
    """
    删除旧机器人数据
    """
    help = "财务系统添加账户 --username --password --role"

    def add_arguments(self, parser):
        parser.add_argument('username',  type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('role', type=int,help='1）财务 2) 股东 3）管理员')
        parser.add_argument('--telephone',
                            default='',
                            )

    @transaction.atomic()
    def handle(self, *args, **options):
        fin = FinanceUserModel()
        username = options['username']
        fin.username = username
        fin.password = options['password']
        fin.role_type = options['role']
        fin.telephone = options.get('telephone','')
        res = FinanceUserModel.objects.filter(username=username).count()
        if res > 0:
            self.stdout.write(self.style.SUCCESS('用户已存在，添加失败！'))
            return
        fin.save()
        self.stdout.write(self.style.SUCCESS('财务系统用户添加成功！'))
