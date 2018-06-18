# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import requests
import json
import time
from django.db import transaction
from users.models import UserCoin, UserRecharge, Coin
from decimal import Decimal
import math

base_url = 'https://blockchain.info/multiaddr?active='
coin_name = 'BTC'


def get_transactions(addresses):
    transactions = {}
    # print('addresses = ', addresses)
    response = requests.get(base_url + addresses)
    # if response.status_code == 500:
    #     raise CommandError(response)
    # print('response = ', response.__dict__)
    datas = json.loads(response.text)
    print('datas = ', datas)
    for item in datas['txs']:
        for out in item['out']:
            addr = out['addr']
            txid = item['hash']

            if addr not in transactions:
                transactions[addr] = []

            # 计算确认数
            confirmations = 0
            if item['double_spend'] is False:
                if 'block_height' in item:
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

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取所有用户ETH地址
        user_btc_address = UserCoin.objects.filter(coin_id=Coin.BTC, user__is_robot=False, user__is_block=False)
        if len(user_btc_address) == 0:
            self.stdout.write(self.style.SUCCESS('无' + coin_name + '地址信息'))
            return True

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_btc_address)) + '条用户' + coin_name + '地址信息'))

        btc_addresses = []
        address_map_uid = {}
        for user_coin in user_btc_address:
            btc_addresses.append(user_coin.address)
            # map address to userid
            address_map_uid[user_coin.address.upper()] = user_coin.user_id

        # 因URL有长度限制，这里分页处理，每页50条
        page_size = 100
        page_total = int(math.ceil(len(btc_addresses) / page_size))
        for i in range(1, page_total + 1):
            start = (i - 1) * page_size
            end = page_size * i

            self.stdout.write(self.style.SUCCESS('正在获取' + str(start) + ' ~ ' + str(end) + '的交易记录'))
            addresses = '|'.join(btc_addresses[start:end])

            transactions = get_transactions(addresses)
            print('transactions = ', transactions)
            self.stdout.write(self.style.SUCCESS('获取到' + str(len(transactions)) + '条交易记录'))
            for address in transactions:
                if len(transactions[address]) == 0:
                    continue

                user_id = address_map_uid[address.upper()]
                user_coin = UserCoin.objects.get(user_id=user_id, coin_id=Coin.BTC)

                # 首次充值获得奖励
                UserRecharge.objects.first_price(user_id)

                valid_trans = 0
                for trans in transactions[address]:
                    tx_id = trans['txid']
                    tx_value = trans['value']
                    confirmations = trans['confirmations']

                    # 过滤一个txid
                    if tx_id == 'd1c8dafc62c897c7eaa77184d9d4a2f7be35823ce4f28824226995343cc27beb':
                        continue

                    # 确认数为0暂时不处理
                    if confirmations < 1:
                        continue

                    # 判断交易hash是否已经存在，存在则忽略该条交易，更新确认数
                    is_exists = UserRecharge.objects.filter(txid=tx_id).count()
                    if is_exists > 0:
                        user_recharge = UserRecharge.objects.get(txid=tx_id)
                        user_recharge.confirmations = confirmations
                        user_recharge.save()
                        continue

                    valid_trans += 1

                    self.stdout.write(self.style.SUCCESS('用户ID=' + str(user_id) + ' 增加 ' + str(tx_value) + ' 个' + coin_name))

                    # 插入充值记录表
                    user_recharge = UserRecharge()
                    user_recharge.user_id = user_id
                    user_recharge.coin_id = Coin.BTC
                    user_recharge.address = address
                    user_recharge.amount = tx_value
                    user_recharge.confirmations = confirmations
                    user_recharge.txid = tx_id
                    user_recharge.trade_at = trans['time']
                    user_recharge.save()

                    # 变更用户余额
                    # user_coin.balance += Decimal(tx_value)
                    # user_coin.save()

                self.stdout.write(self.style.SUCCESS('共 ' + str(valid_trans) + ' 条有效交易记录'))
                self.stdout.write(self.style.SUCCESS(''))
