# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time as format_time
from users.models import UserCoin, UserRecharge, Coin
from base.eth import *
from time import time
import math
from base.app import BaseView


def get_transactions(address):
    """
    根据ETH地址获取交易数据
    :param address:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/chain/transactions2/' + address)

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
                'value': item['ether'],
                'txid': item['hash'],
            }
            txs[addr].append(data)
    return txs


class Command(BaseCommand, BaseView):
    help = "ETH监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        start_time = time()

        # 获取所有用户ETH地址
        # user_eth_address = UserCoin.objects.filter(coin_id=Coin.ETH, user__is_robot=False, user__is_block=False).order_by('id')
        sql = 'SELECT user_id,count(*) as cnt from users_loginrecord GROUP BY user_id HAVING cnt > 50 ORDER BY cnt desc'
        user_eth_address = self.get_all_by_sql(sql)
        eth_address_length = len(user_eth_address)
        if eth_address_length == 0:
            raise CommandError('无地址信息')

        eth_address = []
        address_map_uid = {}
        for user_addr in user_eth_address:
            eth_address.append(user_addr.address)
            address_map_uid[user_addr.address.upper()] = user_addr.user_id

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(eth_address)) + '条用户ETH地址信息'))

        # 因URL有长度限制，这里分页处理，每页80条
        page_size = 1
        page_total = int(math.ceil(len(eth_address) / page_size))
        for i in range(1, page_total + 1):
            start = (i - 1) * page_size
            end = page_size * i

            self.stdout.write(self.style.SUCCESS('正在获取' + str(start) + ' ~ ' + str(end) + '的交易记录'))
            addresses = ','.join(eth_address[start:end])

            transactions = get_transactions(addresses)
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
                    tx_value = trans['value']

                    # 判断交易hash是否已经存在
                    is_exists = UserRecharge.objects.filter(txid=tx_id).count()
                    if is_exists > 0:
                        continue

                    # 插入充值记录表
                    user_recharge = UserRecharge()
                    user_recharge.user_id = user_id
                    user_recharge.coin_id = Coin.ETH
                    user_recharge.address = address
                    user_recharge.amount = tx_value
                    user_recharge.confirmations = 0
                    user_recharge.txid = tx_id
                    user_recharge.trade_at = trans['time']
                    user_recharge.save()

                    valid_trans += 1

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
