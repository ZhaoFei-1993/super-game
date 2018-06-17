# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from users.models import CoinPrice
import json

url_CNY = 'https://api.coinmarketcap.com/v1/ticker/?convert=CNY&limit=0'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
coin_list = ['BTC', 'HAND', 'EOS', 'INT', 'ETH', 'USDT']


def trunc(f, n):
    s1, s2 = str(f).split('.')
    if n == 0:
        return s1
    if n <= len(s2):
        return s1 + '.' + s2[:n]
    return s1 + '.' + s2 + '0' * (n - len(s2))


class Command(BaseCommand):
    help = "更新币价格"

    def handle(self, *args, **options):
        response = requests.get(url_CNY, headers=headers)
        json_list = json.loads(response.text)
        for i in range(0, len(json_list)):
            json_CNY = json_list[i]
            if json_CNY['symbol'] in coin_list:
                symbol = json_CNY['symbol']
                price = float(trunc(json_CNY['price_cny'], 4))

                coin_price = CoinPrice.objects.get(coin_name=symbol)
                coin_price.price = float(trunc(price, 4))
                coin_price.save()

