# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from urllib.parse import urlencode
import requests
import json
from console.models import Address
from users.models import Coin
from django.conf import settings


def created_address():
    params = {
        'password': settings.BTC_WALLET_MAIN_PASSWORD,
        'label': 'gsg_btc_account'
    }
    url = settings.BTC_WALLET_API_URL + '/merchant' + '/' + settings.BTC_WALLET_API_GUID + '/new_address?' + urlencode(params)
    response = requests.get(url)
    json_data = json.loads(response.content)
    return json_data


class Command(BaseCommand):
    help = "分配BTC地址"

    def handle(self, *args, **options):
        # json_data = created_address()
        # print(json_data)

        # if Address.objects.filter(user=User.objects.filter(id=user_id).first()).\
        #         filter(coin=Coin.objects.filter(name='BTC').first()).first() is None:
        #     address_query = Address()
        #     address_query.coin = Coin.objects.filter(name='BTC').first()
        #     address_query.address = json_data['address']
        #     address_query.passphrase = main_password
        #     address_query.user = User.objects.filter(id=user_id).first()
        #     address_query.save()
        #     print('分配成功')
        # else:
        #     print('用户已分配地址')

        for i in range(0, 10):
            json_data = created_address()
            address_query = Address()
            address_query.coin = Coin.objects.filter(name='BTC').first()
            address_query.address = json_data['address']
            address_query.passphrase = settings.BTC_WALLET_MAIN_PASSWORD
            address_query.save()
            print('分配成功')
