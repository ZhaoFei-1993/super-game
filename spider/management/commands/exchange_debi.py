# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from quiz.models import GsgValue
from users.models import Coin, CoinPrice

url = 'https://www.debi.com/Ajax/getTradelog?market=gsg_eth'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "debi"

    def handle(self, *args, **options):
        response = requests.get(url, headers=headers)
        json_dt = response.json()
        value = json_dt['tradelog'][0]['price']

        gsg_value = GsgValue()
        gsg_value.coin = Coin.objects.get(name='GSG')
        gsg_value.house = 'debi'
        gsg_value.value = float(value)
        gsg_value.save()

        print('GSG/ETH价格为: ' + str(value))
