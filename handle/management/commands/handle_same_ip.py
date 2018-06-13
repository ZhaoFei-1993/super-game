# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User
from django.db.models import Q


class Command(BaseCommand):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        ip_list = []
        for user in User.objects.filter(~Q(ip_address=''), is_robot=0):
            if User.objects.filter(ip_address=user.ip_address).count() >= 20:
                if user.ip_address not in ip_list:
                    block_user_list = []
                    ip_list.append(user.ip_address)
                    for block_user in User.objects.filter(ip_address=user.ip_address):
                        block_user.is_block = True
                        block_user.save()
                        block_user_list.append(block_user.id)
                    print('ip:' + user.ip_address + ' ,共封禁 ' + str(len(block_user_list)) + ' 个账号')
                else:
                    pass
        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')
