# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
import time as format_time
from base.eth import *
from time import time


def get_transactions(address):
    """
    根据ETH地址获取交易数据
    :param address:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/chain/transactions/' + address)

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
                'confirmations': json_data['block_number'] - item['blockNumber'],
                'txid': item['hash'],
            }
            txs[addr].append(data)
    return txs


class Command(BaseCommand):
    help = "ETH监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        start = time()
        addresses = [
            '0x5dF698D65baC2ea9FA8B13e4B0AAf5D881f33B02',
            '0x416299AAde6443e6F6e8ab67126e65a7F606eeF5',
            '0x8334a533F0c3f904cA59061faE649a8c596B09aC'
        ]
        transactions = get_transactions(','.join(addresses))
        print('transactions = ', transactions)

        stop = time()
        cost = str(round(stop - start)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost))
