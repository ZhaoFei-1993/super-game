# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *


def get_transactions(address):
    """
    根据ETH地址获取交易数据
    :param address:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/chain/transactions/' + address)
    if len(json_data['data']) == 0:
        return []

    txs = []
    items = json_data['data']
    for item in items:
        time_local = time.localtime(item['received_time'])
        time_dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        data = {
            'time': time_dt,
            'value': item['ether'],
            'confirmations': json_data['block_number'] - item['blockNumber'],
            'txid': item['blockHash'],
        }
        txs.append(data)
    return txs


class Command(BaseCommand):
    help = "ETH监视器"

    def handle(self, *args, **options):
        # 获取所有用户ETH地址
        user_eth_address = UserCoin.objects.filter(coin_id=2)
        if len(user_eth_address) == 0:
            self.stdout.write(self.style.SUCCESS('无地址信息'))
            return True

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_eth_address)) + '条记录'))

        for user_coin in user_eth_address:
            address = user_coin.address
            user_id = user_coin.user_id

            if address == '':
                self.stdout.write(self.style.SUCCESS('用户' + str(user_id) + '无分配ETH地址'))
                continue

            # 根据address获取交易信息
            self.stdout.write(self.style.SUCCESS('正在获取地址为 ' + str(address) + ' 交易记录'))
            transactions = get_transactions(address)
            if len(transactions) == 0:
                self.stdout.write(self.style.SUCCESS('用户' + str(user_id) + '无充值记录'))
                continue

            for transaction in transactions:
                txid = transaction['txid']
                tx_value = transaction['value']
                is_exists = UserRecharge.objects.filter(txid=txid).count()
                if is_exists > 0:
                    continue

                userrecharge = UserRecharge()
                userrecharge.user_id = user_id
                userrecharge.coin = Coin.objects.filter(name='ETH').first()
                userrecharge.address = address
                userrecharge.amount = tx_value
                userrecharge.confirmations = transaction['confirmations']
                userrecharge.txid = txid
                userrecharge.trade_at = transaction['time']
                userrecharge.save()

                user_coin.balance += tx_value
                user_coin.save()
        else:
            print('无数据')
