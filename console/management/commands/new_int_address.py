# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from console.models import Address
from users.models import Coin
from base.eth import *


class Command(BaseCommand):
    help = "生成INT地址"

    def handle(self, *args, **options):
        eth_wallet = Wallet()
        for i in range(0, 10):
            json_data = eth_wallet.post(url='v1/account/new', data=None)
            address_query = Address()
            address_query.coin = Coin.objects.filter(name='INT').first()
            address_query.address = json_data['data']['account']
            address_query.passphrase = json_data['data']['password']
            address_query.save()
            print('分配成功')

