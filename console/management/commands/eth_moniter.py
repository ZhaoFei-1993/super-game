# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
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

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取所有用户ETH地址
        user_eth_address = UserCoin.objects.filter(coin_id=Coin.ETH, user__is_robot=False)
        if len(user_eth_address) == 0:
            self.stdout.write(self.style.SUCCESS('无地址信息'))
            return True

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_eth_address)) + '条用户ETH地址信息'))

        for user_coin in user_eth_address:
            address = user_coin.address
            user_id = user_coin.user_id

            if address == '':
                self.stdout.write(self.style.SUCCESS('用户' + str(user_id) + '无分配ETH地址'))
                continue

            # 根据address获取交易信息
            self.stdout.write(self.style.SUCCESS('正在获取用户 ' + str(user_id) + ' 地址为 ' + str(address) + ' 的交易记录'))
            transactions = get_transactions(address)
            if len(transactions) == 0:
                self.stdout.write(self.style.SUCCESS('用户ID=' + str(user_id) + ' 无充值记录'))
                self.stdout.write(self.style.SUCCESS(''))
                continue

            self.stdout.write(self.style.SUCCESS('接收到 ' + str(len(transactions)) + ' 条交易记录'))

            # 首次充值获得奖励
            UserRecharge.objects.first_price(user_id)

            valid_trans = 0
            for trans in transactions:
                txid = trans['txid']
                tx_value = trans['value']

                # 判断交易hash是否已经存在，存在则忽略该条交易
                is_exists = UserRecharge.objects.filter(txid=txid).count()
                if is_exists > 0:
                    continue

                valid_trans += 1

                # 插入充值记录表
                user_recharge = UserRecharge()
                user_recharge.user_id = user_id
                user_recharge.coin = Coin.objects.filter(name='ETH').first()
                user_recharge.address = address
                user_recharge.amount = tx_value
                user_recharge.confirmations = trans['confirmations']
                user_recharge.txid = txid
                user_recharge.trade_at = trans['time']
                user_recharge.save()

                # 变更用户余额
                user_coin.balance += Decimal(tx_value)
                user_coin.save()

            self.stdout.write(self.style.SUCCESS('共 ' + str(valid_trans) + ' 条有效交易记录'))
            self.stdout.write(self.style.SUCCESS(''))
        else:
            print('无数据')
