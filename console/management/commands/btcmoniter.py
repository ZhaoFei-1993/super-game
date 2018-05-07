# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import json
import time
from users.models import UserCoin, UserRecharge, Coin

user_id = 43
addresses = ['14rE7Jqy4a6P27qWCCsngkUfBxtevZhPHB', '1Ez69SnzzmePmZX3WpEzMKTrcBF2gpNQ55']
base_url = 'https://blockchain.info/multiaddr?active='
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def addtwodimdict(thedict, key_a, key_b, val):
    if key_a in thedict:
        thedict[key_a].update({key_b: val})
    else:
        thedict.update({key_a: {key_b: val}})


def get_txs():
    user_addr = ''
    for address in addresses:
        user_addr = user_addr + address + '|'

    txs = dict()
    response = requests.get(base_url + user_addr, headers=headers)
    datas = json.loads(response.text)
    for item in datas['txs']:
        for out in item['out']:
            addr = out['addr']
            txid = item['hash']

            # 计算确认数
            confirmations = 0
            if item['double_spend'] is False:
                if item['block_height']:
                    confirmations = datas['info']['latest_block']['height'] - item['block_height'] + 1

            time_local = time.localtime(item['time'])
            time_dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

            data = {
                        'time': time_dt,
                        'value': out['value'] / datas['info']['conversion'],
                        'confirmations': confirmations
                    }
            addtwodimdict(txs, addr, txid, data)
    return txs


class Command(BaseCommand):
    help = "BTC监视器"

    def handle(self, *args, **options):
        txs_list = get_txs()
        for address in addresses[0:]:
            for key, value in txs_list[address].items():
                print(key, value)
                if UserRecharge.objects.filter(txid=key).first() is None:
                    userrecharge = UserRecharge()
                    userrecharge.user_id = user_id
                    userrecharge.coin = Coin.objects.filter(name='BTC').first()
                    userrecharge.address = address
                    userrecharge.amount = value['value']
                    userrecharge.confirmations = value['confirmations']
                    userrecharge.txid = key
                    userrecharge.trade_at = value['time']
                    userrecharge.save()

                    usercoin = UserCoin.objects.filter(user_id=user_id).\
                        filter(coin=Coin.objects.filter(name='BTC').first()).first()
                    usercoin.balance = usercoin.balance + UserRecharge.objects.filter(txid=key).first().amount
                    usercoin.save()

                    print('----------------')
                else:
                    print('已经存在')
                    print('----------------')
