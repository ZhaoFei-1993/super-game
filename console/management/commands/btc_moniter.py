# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import requests
import json
import time
from users.models import UserCoin, UserRecharge, Coin
from decimal import Decimal

base_url = 'https://blockchain.info/multiaddr?active='
coin_name = 'BTC'


def get_transactions(addresses):
    transactions = {}
    response = requests.get(base_url + addresses)
    datas = json.loads(response.text)
    for item in datas['txs']:
        for out in item['out']:
            addr = out['addr']
            txid = item['hash']

            if addr not in transactions:
                transactions[addr] = []

            # 计算确认数
            confirmations = 0
            if item['double_spend'] is False:
                if item['block_height']:
                    confirmations = datas['info']['latest_block']['height'] - item['block_height'] + 1

            time_local = time.localtime(item['time'])
            time_dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)

            transactions[addr].append({
                'txid': txid,
                'time': time_dt,
                'value': out['value'] / datas['info']['conversion'],
                'confirmations': confirmations
            })
    return transactions


class Command(BaseCommand):
    help = "BTC监视器"

    def handle(self, *args, **options):
        # 获取所有用户ETH地址
        user_btc_address = UserCoin.objects.filter(coin_id=Coin.BTC, user__is_robot=False)
        if len(user_btc_address) == 0:
            self.stdout.write(self.style.SUCCESS('无' + coin_name + '地址信息'))
            return True

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_btc_address)) + '条用户' + coin_name + '地址信息'))

        btc_addresses = []
        address_map_uid = {}
        for user_coin in user_btc_address:
            btc_addresses.append(user_coin.address)
            # map address to userid
            address_map_uid[user_coin.address] = user_coin.user_id
        addresses = '|'.join(btc_addresses)

        self.stdout.write(self.style.SUCCESS('正在获取所有用户' + coin_name + '地址交易记录'))
        transactions = get_transactions(addresses)
        for address in transactions:
            if len(transactions[address]) == 0:
                continue

            # 首次充值获得奖励
            UserRecharge.objects.first_price(address_map_uid[address])

            valid_trans = 0
            for transaction in transactions[address]:
                tx_id = transaction.txid
                tx_value = transaction.value

                # 判断交易hash是否已经存在，存在则忽略该条交易
                is_exists = UserRecharge.objects.filter(txid=tx_id).count()
                if is_exists > 0:
                    continue

                valid_trans += 1

                # 插入充值记录表
                user_recharge = UserRecharge()
                user_recharge.user_id = address_map_uid[address]
                user_recharge.coin_id = Coin.BTC
                user_recharge.address = address
                user_recharge.amount = tx_value
                user_recharge.confirmations = transaction.confirmations
                user_recharge.txid = tx_id
                user_recharge.trade_at = transaction.time
                user_recharge.save()

                # 变更用户余额
                user_coin.balance += Decimal(tx_value)
                user_coin.save()

            self.stdout.write(self.style.SUCCESS('共 ' + str(valid_trans) + ' 条有效交易记录'))
            self.stdout.write(self.style.SUCCESS(''))
