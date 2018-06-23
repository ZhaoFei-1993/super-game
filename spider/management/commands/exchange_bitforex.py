# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from quiz.models import GsgValue
from users.models import Coin, CoinPrice

url = 'https://www.bitforex.com/server/cointrade.act?cmd=getTickers&currencyCode=usdt'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "debi"

    def handle(self, *args, **options):
        response = requests.get(url, headers=headers)
        json_dt = response.json()
        for dt in json_dt['data']:
            if dt['busitype'] == 'coin-usdt-btc':
                value = dt['last']
                value_rmb = float(value) * float(CoinPrice.objects.get(coin_name='USDT').price)

        gsg_value = GsgValue()
        gsg_value.coin = Coin.objects.get(name='BTC')
        gsg_value.house = 'bitforex'
        gsg_value.value = float(value)
        gsg_value.value_rmb = value_rmb
        gsg_value.save()

        print('BTC/USDT价格为: ' + str(value) + ' 对应rmb价格为: ' + str(value_rmb))