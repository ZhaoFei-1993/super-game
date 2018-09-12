# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from base.eth import Wallet
import random


class Command(BaseCommand):
    help = "ETH及代币转账测试"

    @transaction.atomic()
    def handle(self, *args, **options):
        eth_wallet = Wallet()
        data = {
            'to': '0x13A3c13d7Ebbd9f2856779c4Ae46A8F0dAe824cE',
            'amount': str(random.randint(1, 10)),
        }
        json_data = eth_wallet.post(url='v1/transaction/token/send/gsg', data=data)
        print('json_data = ', json_data)
