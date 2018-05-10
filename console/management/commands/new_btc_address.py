# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from urllib.parse import urlencode
import requests
import json
from console.models import Address
from users.models import Coin, User

user_id = 42

localhost = '127.0.0.1'
base_url = 'http://' + localhost + ':3000'
guid = '887c59bc-4895-415b-a090-98b0a1710837'
main_password = 'wecom$888'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def created_address():
    params = {
        'password': main_password,
        'label': user_id
    }
    url = base_url + '/merchant' + '/' + guid + '/new_address?' + urlencode(params)
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
            address_query.passphrase = main_password
            address_query.save()
            print('分配成功')



