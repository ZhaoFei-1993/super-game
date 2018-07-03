# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import requests
import json
import time as format_time
from time import time
from django.db import transaction
from users.models import UserCoin, UserRecharge, Coin, CoinDetail
from decimal import Decimal
import math

base_url = 'https://blockchain.info/multiaddr?active='
omni_url = 'https://api.omniexplorer.info/v1/transaction/tx/'


def get_transactions(addresses):
    transactions = {}
    # print('addresses = ', addresses)
    response = requests.get(base_url + addresses)
    if response.status_code == 500 or response.status_code == 400:
        print('Error = ', response.__dict__)
        return []
        # raise CommandError(response)
    # print('response = ', response.__dict__)
    datas = json.loads(response.text)
    for item in datas['txs']:
        if item['result'] <= 0:
            continue

        for out in item['out']:
            if 'addr' not in out:
                continue

            addr = out['addr']
            txid = item['hash']

            if addr not in transactions:
                transactions[addr] = []

            # 计算确认数
            confirmations = 0
            if item['double_spend'] is False:
                if 'block_height' in item:
                    confirmations = datas['info']['latest_block']['height'] - item['block_height'] + 1

            time_local = format_time.localtime(item['time'])
            time_dt = format_time.strftime("%Y-%m-%d %H:%M:%S", time_local)

            # 判断是否USDT
            usdt_resp = requests.get(omni_url + txid, headers={'content-type': 'application/json'})
            usdt_data = json.loads(usdt_resp.text)
            if usdt_data['type'] != 'Error - Not Found':
                transactions[addr].append({
                    'txid': txid,
                    'time': time_dt,
                    'value': usdt_data['amount'],
                    'confirmations': confirmations,
                    'coin': 'USDT',
                })
            else:
                transactions[addr].append({
                    'txid': txid,
                    'time': time_dt,
                    'value': out['value'] / datas['info']['conversion'],
                    'confirmations': confirmations,
                    'coin': 'BTC',
                })
    return transactions


class Command(BaseCommand):
    help = "BTC监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        start_time = time()

        # 获取所有用户ETH地址
        user_btc_address = UserCoin.objects.filter(coin_id=Coin.BTC, user__is_robot=False, user__is_block=False).order_by('id')
        if len(user_btc_address) == 0:
            raise CommandError('无比特币地址信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_btc_address)) + '条用户地址信息'))

        btc_addresses = []
        address_map_uid = {}
        for user_coin in user_btc_address:
            btc_addresses.append(user_coin.address)
            # map address to userid
            address_map_uid[user_coin.address.upper()] = user_coin.user_id

        # 过滤掉测试数据的TXID
        out_tx = [
            'cc8fcbb094e72bedf5ca7a5230f66b29915522f3395e846fe5acb713ebd88fee',
            'd1c8dafc62c897c7eaa77184d9d4a2f7be35823ce4f28824226995343cc27beb',
            '1dd7ff837dc6dad3e4a2cf696f8035a258b6a35c9f474e76505c0aa8d63a31bf',
            'bc1d923b4efa67541dba52a521cfdc67193e5ae0e1943814b5afa00dcb493dcc',
            'e92e30731ae2f7d06cd202483f5e0e519b821c8ed888a300d9d9d722518d637f',
            '40b7f0e5e0f2868f1d74dbe700f8b71d95114a55f1ec9d396543655942653281',
            'b3c6d8bebefc07ca182873b8e4a0840587dc198cdfebf68c65e30fd7f12afe49',
            'a9a8a0d44624a5746ec91406c7356155e731babb374033dc3a86f99cdc853766',
            'd180c0a3a76e160765eda4fbbc8450ee37f6b24e1d1cb15a3105e0519d2c2342',
            'e5a74a1fc6c57b6acf08691503e867381d93b524045190f14a1da25efc7f35af',
            'b193e0a7fee20bfda1202ec3c7e136f72d9b2926327fe17cf1db6cbeaf1f002a',
            '77c6ccab03443fa13fe6ecb68939c4ec433575168054307722d3966c0e3f8eb4',
        ]

        # 因URL有长度限制，这里分页处理，每页50条
        page_size = 80
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

                if address.upper() not in address_map_uid:
                    continue

                user_id = address_map_uid[address.upper()]

                # 首次充值获得奖励
                UserRecharge.objects.first_price(user_id)

                valid_trans = 0
                for trans in transactions[address]:
                    tx_id = trans['txid']
                    tx_value = trans['value']
                    confirmations = trans['confirmations']

                    # 过滤掉测试数据的TXID
                    if tx_id in out_tx:
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

                    self.stdout.write(self.style.SUCCESS('用户ID=' + str(user_id) + ' 增加 ' + str(tx_value) + ' 个' + trans['coin']))

                    coin_id = Coin.BTC
                    if trans['coin'] == 'USDT':
                        coin_id = Coin.USDT

                    # 插入充值记录表
                    user_recharge = UserRecharge()
                    user_recharge.user_id = user_id
                    user_recharge.coin_id = coin_id
                    user_recharge.address = address
                    user_recharge.amount = tx_value
                    user_recharge.confirmations = confirmations
                    user_recharge.txid = tx_id
                    user_recharge.trade_at = trans['time']
                    user_recharge.save()

                    # 变更用户余额
                    user_coin_exists = UserCoin.objects.filter(user_id=user_id, coin_id=coin_id).count()
                    if user_coin_exists == 0:
                        user_btc_coin = UserCoin.objects.get(user_id=user_id, coin_id=Coin.BTC)
                        ucoin = UserCoin()
                        ucoin.balance = 0
                        ucoin.is_opt = 0
                        ucoin.is_bet = 0
                        ucoin.address = user_btc_coin.address
                        ucoin.coin_id = coin_id
                        ucoin.user_id = user_id
                        ucoin.save()

                    user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
                    user_coin.balance += Decimal(tx_value)
                    user_coin.save()

                    # 用户余额变更记录
                    coin_detail = CoinDetail()
                    coin_detail.user_id = user_id
                    coin_detail.coin_name = trans['coin']
                    coin_detail.amount = tx_value
                    coin_detail.rest = user_coin.balance
                    coin_detail.sources = CoinDetail.RECHARGE
                    coin_detail.save()

                self.stdout.write(self.style.SUCCESS('共 ' + str(valid_trans) + ' 条有效交易记录'))
                self.stdout.write(self.style.SUCCESS(''))

        stop_time = time()
        cost_time = str(round(stop_time - start_time)) + '秒'
        self.stdout.write(self.style.SUCCESS('执行完成。耗时：' + cost_time))
