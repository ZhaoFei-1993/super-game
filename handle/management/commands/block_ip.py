# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, UserCoin


class Command(BaseCommand):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        ip_list = []
        for usercoin in UserCoin.objects.filter(coin_id=9):
            if usercoin.user.id in ip_list:
                print("user_id=================================", usercoin.user.id)
            else:
                ip_list.append(usercoin.user.id)
        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')