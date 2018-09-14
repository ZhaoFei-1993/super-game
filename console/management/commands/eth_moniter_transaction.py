# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from users.models import UserRecharge, Coin, UserCoin, CoinDetail, User
from base.eth import *
from decimal import Decimal


def get_transaction(transaction_hash):
    """
    根据transactionHash获取交易数据
    :param transaction_hash:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/transaction/' + transaction_hash)
    if json_data['code'] > 0:
        raise CommandError(json_data['message'] + ' tx = ' + transaction_hash)

    return json_data['data']


class Command(BaseCommand):
    help = "ETH及代币充值监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        confirm_number = settings.ETH_CONFIRMATIONS

        # 获取所有ETH及代币ID
        eth_token_ids = []
        coins = Coin.objects.get_all()
        coin_names = []
        map_coin = {}
        for coin in coins:
            if coin.is_eth_erc20:
                eth_token_ids.append(coin.id)
                coin_names.append(coin.name)
                map_coin[coin.id] = coin

        # 获取所有用户ETH交易hash，只获取交易确认数小于指定值的数据
        user_recharges = UserRecharge.objects.filter(coin_id__in=eth_token_ids, confirmations__lt=confirm_number)
        if len(user_recharges) == 0:
            raise CommandError('无充值信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_recharges)) + '条充值记录'))

        cnt_confirm = 0
        for recharge in user_recharges:
            txid = recharge.txid
            user_id = recharge.user_id
            coin = map_coin[recharge.coin_id]

            trans = get_transaction(txid)
            confirmations = trans['confirmations']

            if confirmations < confirm_number:
                self.stdout.write(self.style.SUCCESS(txid + ' 确认数未达标'))
                continue

            recharge.confirmations = confirmations
            recharge.save()

            # 首次充值获得奖励
            UserRecharge.objects.first_price(user_id)

            # 用户充值成功
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin.id)
            user_coin.balance += Decimal(recharge.amount)
            user_coin.save()

            # 用户余额变更记录
            coin_detail = CoinDetail()
            coin_detail.user_id = user_id
            coin_detail.coin_name = coin.name
            coin_detail.amount = recharge.amount
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.RECHARGE
            coin_detail.save()

            # SOC赠送活动
            if coin.id == Coin.SOC:
                user = User.objects.get(pk=user_id)
                UserRecharge.objects.soc_gift_event(user)

            self.stdout.write(self.style.SUCCESS('确认一笔 ' + str(coin.name) + ' 充值，TXID=' + txid))

            cnt_confirm += 1

        self.stdout.write(self.style.SUCCESS('共确认 ' + str(cnt_confirm) + ' 条有效充值记录'))
        self.stdout.write(self.style.SUCCESS(''))
