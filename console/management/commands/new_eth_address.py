# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import json
from console.models import Address
from users.models import Coin, User
from base.eth import *


user_id = 43

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "分配ETH地址"

    def handle(self, *args, **options):
        eth_wallet = Wallet()
        # json_data = eth_wallet.post(url='v1/account/new', data=None)

        # if Address.objects.filter(user=User.objects.filter(id=user_id).first()). \
        #         filter(coin=Coin.objects.filter(name='ETH').first()).first() is None:
        #     address_query = Address()
        #     address_query.coin = Coin.objects.filter(name='ETH').first()
        #     address_query.address = json_data['data']['account']
        #     address_query.passphrase = json_data['data']['password']
        #     address_query.user = User.objects.filter(id=user_id).first()
        #     address_query.save()
        #     print('分配成功')
        # else:
        #     print('用户已分配地址')

        for i in range(0, 10):
            json_data = eth_wallet.post(url='v1/account/new', data=None)
            address_query = Address()
            address_query.coin = Coin.objects.filter(name='ETH').first()
            address_query.address = json_data['data']['account']
            address_query.passphrase = json_data['data']['password']
            address_query.save()
            print('分配成功')
