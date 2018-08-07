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
coin_list = ['BTC', 'HAND', 'EOS', 'INT', 'ETH', 'USDT']


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
        date_ymd = datetime.datetime.now().strftime('%Y-%m-%d')
        start_with = datetime.datetime(int(date_ymd.split('-')[0]), int(date_ymd.split('-')[1]),
                                       int(date_ymd.split('-')[2]), 0, 0, 0)
        end_with = datetime.datetime(int(date_ymd.split('-')[0]), int(date_ymd.split('-')[1]),
                                     int(date_ymd.split('-')[2]), 23, 59, 59)
        if CoinPriceZero.objects.filter(updated_at__range=(start_with, end_with)).count() == len(coin_list):
            print('无需更新')
        else:
            for coin_name in coin_list:
                if CoinPriceZero.objects.filter(updated_at__range=(start_with, end_with), coin_name=coin_name).exists():
                    print('已经更新为最新')
                else:
                    response = requests.get(url_CNY, headers=headers)
                    json_list = json.loads(response.text)
                    for i in range(0, len(json_list)):
                        json_CNY = json_list[i]
                        if json_CNY['symbol'] == coin_name:
                            last_updated = datetime.datetime.utcfromtimestamp(
                                int(json_CNY['last_updated'])) + datetime.timedelta(hours=8)
                            update_time = datetime.datetime.strptime(date_ymd + ' 00:00:00', "%Y-%m-%d %H:%M:%S")
                            if last_updated > update_time:
                                price = float(trunc(json_CNY['price_cny'], 4))
                                price_usd = float(trunc(json_CNY['price_usd'], 4))

                                coin_price = CoinPriceZero()
                                coin_price.coin_name = coin_name
                                coin_price.platform_name = 'coinmarketcap'
                                coin_price.price = float(trunc(price, 4))
                                coin_price.price_usd = float(trunc(price_usd, 4))
                                coin_price.save()
                                coin_price.updated_at = update_time
                                coin_price.updated_at_true = last_updated
                                coin_price.save()
                                print(coin_name, '价格已经变更')
