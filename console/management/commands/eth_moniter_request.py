# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import requests
import json
import time as format_time
from time import time
from django.db import transaction
from users.models import UserCoin, UserRecharge, Coin, CoinDetail
from decimal import Decimal
import math

base_url = 'https://api.etherscan.io/api?module=account&action=tokentx&page=1&contractaddress=0x48c1b2f3efa85fbafb2ab951bf4ba860a08cdbb7&sort=asc&apikey=EWDNKCP1EY3D645KI2S4CKR1JKVM9RW6VE&address='


def get_transactions(addresses):
    transactions = {}
    response = requests.get(base_url + addresses)
    datas = json.loads(response.text)
    print('datas = ', datas)
    return transactions


class Command(BaseCommand):
    help = "BTC监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        start_time = time()

        # 获取所有用户ETH地址
        user_btc_address = UserCoin.objects.filter(coin_id=Coin.INT, user__is_robot=False, user__is_block=False).order_by('id')
        if len(user_btc_address) == 0:
            raise CommandError('无地址信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_btc_address)) + '条用户地址信息'))

        for user_coin in user_btc_address:
            get_transactions(user_coin.address)

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
