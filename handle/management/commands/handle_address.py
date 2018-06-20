# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from api.settings import BASE_DIR
import os
from django.db.models import Q
from users.models import UserRecharge, UserCoin
from console.models import Address


class Command(BaseCommand):
    help = "处理地址"

    def handle(self, *args, **options):
        os.chdir(BASE_DIR + '/cache')
        i = 1
        a = []
        with open('corrent_address.txt', 'r+') as f:
            for line in f:
                line_dt = line.strip().split(',')
                addres = line_dt[0]
                address = Address.objects.get(address=str(addres))
                address_user_id = address.user
                coin_user_id = UserCoin.objects.filter(~Q(user_id=address_user_id), address=str(addres))
                for user_id in coin_user_id:
                    user_recharge = UserRecharge.objects.filter(user=user_id.user, coin=user_id.coin).count()
                    if user_recharge != 0:
                        print("addres=========================", addres)
                        a.append(addres)
                    else:
                        user_id.address = ''
                        # user_id.save()
                    print("==========================i=========================", i)
                    i += 1
                print("==========================i=========================", a)

