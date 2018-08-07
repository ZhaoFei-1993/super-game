# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from users.models import CoinPrice, CoinPriceZero
import json
import datetime
import time

url_CNY = 'https://api.coinmarketcap.com/v1/ticker/?convert=CNY&limit=0'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}
coin_list = ['BTC', 'EOS', 'INT', 'ETH', 'USDT']


def trunc(f, n):
    s1, s2 = str(f).split('.')
    if n == 0:
        return s1
    if n <= len(s2):
        return s1 + '.' + s2[:n]
    return s1 + '.' + s2 + '0' * (n - len(s2))


class Command(BaseCommand):
    help = "更新0点币价格"

    def handle(self, *args, **options):
        for coin_name in coin_list:
            coin_price = CoinPriceZero.objects.get(coin_name=coin_name)
            coin_update_at_ymd = coin_price.updated_at.strftime('%Y-%m-%d') + ' 23:59:00'
            compare_time = datetime.datetime.strptime(coin_update_at_ymd, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() > compare_time:
                response = requests.get(url_CNY, headers=headers)
                json_list = json.loads(response.text)
                for i in range(0, len(json_list)):
                    json_CNY = json_list[i]
                    if json_CNY['symbol'] == coin_name:
                        last_updated = datetime.datetime.utcfromtimestamp(int(json_CNY['last_updated']))
                        update_time = datetime.datetime.strptime((compare_time + datetime.timedelta(days=1)).strftime('%Y-%m-%d') + ' 00:00:00', "%Y-%m-%d %H:%M:%S")
                        if last_updated > update_time:
                            price = float(trunc(json_CNY['price_cny'], 4))
                            price_usd = float(trunc(json_CNY['price_usd'], 4))

                            coin_price.price = float(trunc(price, 4))
                            coin_price.price_usd = float(trunc(price_usd, 4))
                            coin_price.save()
                            coin_price.updated_at = update_time
                            coin_price.updated_at_true = last_updated
                            coin_price.save()
                            print(coin_name, '价格已经变更')
            else:
                print('无需更新')
