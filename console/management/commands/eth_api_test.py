# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from base.eth import *


def get_transactions():
    """
    根据ETH地址获取交易数据
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/transaction/0xe88cac9002416252431dc995d5e3db1fb0e891635b6798c8ff3b6e0ea0125f7f')
    print(json_data)
    if len(json_data['data']) == 0:
        return []

    # print(json_data)


class Command(BaseCommand):
    help = "ETH API test"

    @transaction.atomic()
    def handle(self, *args, **options):
        get_transactions()
