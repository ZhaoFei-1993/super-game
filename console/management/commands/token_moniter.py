# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *


def get_transactions(coin, address):
    """
    根据HAND地址获取交易数据
    :param coin
    :param address:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/account/' + coin.lower() + '/transaction/' + address)
    if len(json_data['data']) == 0:
        return []

    txs = []
    items = json_data['data']
    for item in items:
        time_local = time.localtime(item['received_time'])
        time_dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        data = {
            'time': time_dt,
            'value': item['value'],
            'confirmations': item['confirmations'],
            'txid': item['txid'],
        }
        txs.append(data)
    return txs


class Command(BaseCommand):
    help = "ETH TOKEN监视器"

    def add_arguments(self, parser):
        parser.add_argument('coin', type=str)

    @transaction.atomic()
    def handle(self, *args, **options):
        coin_name = options['coin'].upper()

        try:
            coin = Coin.objects.get(name=coin_name)
        except Coin.DoesNotExist:
            raise CommandError(coin_name + '无效')

        coin_id = coin.id
        coin_name = coin.name
        self.stdout.write(self.style.SUCCESS('************正在获取' + coin_name + '交易数据***************'))
        self.stdout.write(self.style.SUCCESS(''))

        # 获取所有用户ETH地址
        user_eth_address = UserCoin.objects.filter(coin_id=coin_id, user__is_robot=False, user__is_block=False).order_by('id')
        if len(user_eth_address) == 0:
            raise CommandError('无地址信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_eth_address)) + '条用户' + coin_name + '地址信息'))

        for user_coin in user_eth_address:
            address = user_coin.address
            user_id = user_coin.user_id

            if address == '':
                self.stdout.write(self.style.SUCCESS('用户' + str(user_id) + '无分配' + coin_name + '地址'))
                continue

            # 根据address获取交易信息
            # self.stdout.write(self.style.SUCCESS('正在获取用户 ' + str(user_id) + ' 地址为 ' + str(address) + ' 的交易记录'))
            transactions = get_transactions(coin.name, address)
            if len(transactions) == 0:
                # self.stdout.write(self.style.SUCCESS('用户ID=' + str(user_id) + ' 无充值记录'))
                continue

            self.stdout.write(self.style.SUCCESS('接收到 ' + str(len(transactions)) + ' 条交易记录'))

            valid_trans = 0
            for trans in transactions:
                txid = trans['txid']
                tx_value = int(trans['value'])

                is_exists = UserRecharge.objects.filter(txid=txid).count()
                if is_exists > 0:
                    continue

                user_recharge = UserRecharge()
                user_recharge.user_id = user_id
                user_recharge.coin = coin
                user_recharge.address = address
                user_recharge.amount = tx_value
                user_recharge.confirmations = 0
                user_recharge.txid = txid
                user_recharge.trade_at = trans['time']
                user_recharge.save()

                valid_trans += 1

            self.stdout.write(self.style.SUCCESS('共 ' + str(valid_trans) + ' 条有效交易记录'))
