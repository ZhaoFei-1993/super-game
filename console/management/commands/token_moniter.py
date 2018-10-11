# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time as format_time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *
from time import time
import math
from decimal import Decimal


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

    txs = {}
    items = json_data['data']
    for addr in items:
        txs[addr] = []
        transactions = items[addr]
        if len(transactions) == 0:
            continue

        for item in transactions:
            time_local = format_time.localtime(item['received_time'])
            time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            data = {
                'time': time_dt,
                'value': item['value'],
                'txid': item['txid'],
            }
            txs[addr].append(data)
    return txs


class Command(BaseCommand):
    help = "ETH TOKEN监视器"

    def add_arguments(self, parser):
        parser.add_argument('coin', type=str)

    @transaction.atomic()
    def handle(self, *args, **options):
        start_time = time()
        coin_name = options['coin'].upper()

        try:
            coin = Coin.objects.get(name=coin_name)
        except Coin.DoesNotExist:
            raise CommandError(coin_name + '无效')

        coin_decimal = 1
        if coin_name == 'INT':
            coin_decimal = 1000000
        elif coin_name == 'HAND':
            coin_decimal = 1
        elif coin_name == 'GSG':
            coin_decimal = 10000000000
        elif coin_name == 'DB':
            coin_decimal = 1000000
        elif coin_name == 'SOC':
            coin_decimal = 1000000000000000000

        coin_id = coin.id
        coin_name = coin.name
        self.stdout.write(self.style.SUCCESS('************正在获取' + coin_name + '交易数据***************'))
        self.stdout.write(self.style.SUCCESS(''))

        # 获取所有用户ETH地址
        user_eth_address = UserCoin.objects.filter(coin_id=coin_id, user__is_robot=False, user__is_block=False).order_by('id')
        if len(user_eth_address) == 0:
            raise CommandError('无地址信息')

        eth_address = []
        address_map_uid = {}
        for user_addr in user_eth_address:
            eth_address.append(user_addr.address)
            address_map_uid[user_addr.address.upper()] = user_addr.user_id

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_eth_address)) + '条用户' + coin_name + '地址信息'))

        # 因URL有长度限制，这里分页处理，每页100条
        page_size = 100
        page_total = int(math.ceil(len(eth_address) / page_size))
        for i in range(1, page_total + 1):
            start = (i - 1) * page_size
            end = page_size * i

            self.stdout.write(self.style.SUCCESS('正在获取' + str(start) + ' ~ ' + str(end) + '的交易记录'))
            addresses = ','.join(eth_address[start:end])

            transactions = get_transactions(coin_name, addresses)
            if not transactions:
                self.stdout.write(self.style.SUCCESS('未获取到任何交易记录'))
                self.stdout.write(self.style.SUCCESS(''))
                continue

            for address in transactions:
                len_trans = len(transactions[address])
                if len_trans == 0:
                    continue

                self.stdout.write(self.style.SUCCESS(address + '获取到' + str(len_trans) + '交易记录'))
                self.stdout.write(self.style.SUCCESS(''))
                user_id = address_map_uid[address.upper()]

                # 首次充值获得奖励
                UserRecharge.objects.first_price(user_id)

                valid_trans = 0
                for trans in transactions[address]:
                    tx_id = trans['txid']
                    tx_value = Decimal(trans['value'])

                    # 判断交易hash是否已经存在
                    is_exists = UserRecharge.objects.filter(txid=tx_id).count()
                    if is_exists > 0:
                        continue

                    # 插入充值记录表
                    user_recharge = UserRecharge()
                    user_recharge.user_id = user_id
                    user_recharge.coin_id = coin_id
                    user_recharge.address = address
                    user_recharge.amount = tx_value / Decimal(coin_decimal)
                    user_recharge.confirmations = 0
                    user_recharge.txid = tx_id
                    user_recharge.trade_at = trans['time']
                    user_recharge.save()

                    valid_trans += 1

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
