# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, LoginRecord
from collections import Counter


class Command(BaseCommand):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        # a = [1, 2, 3, 4, 4, 5, 1, 1, 8, 9, 9]
        # counter = Counter(a)
        # print(counter.most_common(1)[0][0])

        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        for user in User.objects.filter(ip_address=''):
            login_address_list = []
            for login_address in LoginRecord.objects.filter(user=user):
                login_address_list.append(login_address.ip)
            address_counter = Counter(login_address_list)
            commonly_address = address_counter.most_common(1)[0][0]
            user.ip_address = commonly_address
            user.save()
            print('user:' + str(user.id) + ' ,的ip地址为: ' + commonly_address)
        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')
