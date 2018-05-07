# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

import time
from users.models import User, UserCoin, UserRecharge, Coin
from base.eth import *

user_id = 43
addresses = ['0xf8158a2823bdd6b0b3a3a987cde8cfa308506abc']


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


def addtwodimdict(thedict, key_a, key_b, val):
    if key_a in thedict:
        thedict[key_a].update({key_b: val})
    else:
        thedict.update({key_a: {key_b: val}})


def get_txs():
    txs = dict()
    eth_wallet = Wallet()
    for address in addresses:
        json_data = eth_wallet.get(url='v1/chain/transactions/' + address)
        print(json_data)
        if len(json_data['data']) == 0:
            continue
        items = json_data['data']
        for item in items:
            time_local = time.localtime(item['received_time'])
            time_dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            data = {
                'time': time_dt,
                'value': item['ether'],
                'confirmations': json_data['block_number'] - item['blockNumber']
            }
            addtwodimdict(txs, address, item['blockHash'], data)
    return txs


class Command(BaseCommand):
    help = "ETH监视器"

    def handle(self, *args, **options):
        txs_list = get_txs()
        print(txs_list)
        if txs_list:
            for address in addresses[0:]:
                for key, value in txs_list[address].items():
                    print(key, value)
                    if UserRecharge.objects.filter(txid=key).first() is None:
                        userrecharge = UserRecharge()
                        userrecharge.user_id = user_id
                        userrecharge.coin = Coin.objects.filter(name='ETH').first()
                        userrecharge.address = address
                        userrecharge.amount = value['value']
                        userrecharge.confirmations = value['confirmations']
                        userrecharge.txid = key
                        userrecharge.trade_at = value['time']
                        userrecharge.save()

                        usercoin = UserCoin.objects.filter(user_id=user_id).\
                            filter(coin=Coin.objects.filter(name='ETH').first()).first()
                        usercoin.balance = usercoin.balance + UserRecharge.objects.filter(txid=key).first().amount
                        usercoin.save()

                        print('----------------')
                    else:
                        print('已经存在')
                        print('----------------')
        else:
            print('无数据')


