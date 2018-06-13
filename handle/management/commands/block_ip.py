# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        ip_list = []
        i = 1
        for user in User.objects.all():
            ip_address = str(user.ip_address)
            if ip_address != '':
                ip1, ip2, ip3, ip4 = ip_address.split('.')
                startswith = ip1 + '.' + ip2 + '.' + ip3 + '.'
                if User.objects.filter(ip_address__startswith=startswith).count() >= 15:
                    if user.ip_address not in ip_list:
                        block_user_list = []
                        ip_list.append(user.ip_address)
                        for block_user in User.objects.filter(ip_address=user.ip_address):
                            i += 1
                            block_user.is_block = True
                            block_user.save()
                            block_user_list.append(block_user.id)
                        print('ip:' + user.ip_address + ' ,共封禁 ' + str(len(block_user_list)) + ' 个账号')
                else:
                    pass
        print('>>>>>>>>>>>>>>>>>>>>>>>> 狗带了', i, '个用户 >>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')