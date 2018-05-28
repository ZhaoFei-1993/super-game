# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from console.models import Address
from users.models import Coin
from base.eth import *


class Command(BaseCommand):
    help = "分配ETH地址"
    max_address = 1000

    def handle(self, *args, **options):
        eth_wallet = Wallet()

        self.stdout.write(self.style.SUCCESS('****************正在获取ETH地址******************'))

        idx = 1
        for i in range(0, self.max_address):
            json_data = eth_wallet.post(url='v1/account/new', data=None)
            if json_data['code'] != 0:
                print(json_data['message'])
                return False

            address_query = Address()
            address_query.coin = Coin.objects.filter(name='ETH').first()
            address_query.address = json_data['data']['account']
            address_query.passphrase = json_data['data']['password']
            address_query.save()

            print('分配成功 ' + str(idx))
            idx += 1

        self.stdout.write(self.style.SUCCESS('成功生成 ' + str(self.max_address) + ' 条ETH地址'))
