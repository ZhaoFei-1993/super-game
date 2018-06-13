# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, IntInvitation
from django.db.models import Q


class Command(BaseCommand):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        ip_list = []
        for user in IntInvitation.objects.filter(inviter_id=2638):
            user_id = user.invitee
            user_info = User.objects.get(id=user_id)
            ip_address = user_info.ip_address
            if User.objects.filter(ip_address=ip_address).count() >= 10 and ip_address != '':
                if user_info.ip_address not in ip_list:
                    block_user_list = []
                    ip_list.append(user_info.ip_address)
                    for block_user in User.objects.filter(ip_address=user_info.ip_address):
                        block_user.is_block = True
                        # block_user.save()
                        block_user_list.append(block_user.id)
                    print('ip:' + user_info.ip_address + ' ,共封禁 ' + str(len(block_user_list)) + ' 个账号')
                else:
                    pass
        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')
