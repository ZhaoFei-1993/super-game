# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from users.models import UserRecharge, Coin, UserCoin, CoinDetail
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
    help = "ETH交易信息监视器"

    def add_arguments(self, parser):
        parser.add_argument('coin', type=str)

    @transaction.atomic()
    def handle(self, *args, **options):
        coin_name = options['coin']

        try:
            coin = Coin.objects.get(name=coin_name)
        except Coin.DoesNotExist:
            raise CommandError('coin名称无效')

        # 获取所有用户ETH交易hash，只获取交易确认数小于指定值的数据
        user_recharges = UserRecharge.objects.filter(coin_id=coin.id, confirmations__lt=settings.ETH_CONFIRMATIONS)
        if len(user_recharges) == 0:
            raise CommandError('无交易信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_recharges)) + '条用户ETH交易信息'))

        cnt_confirm = 0
        for recharge in user_recharges:
            txid = recharge.txid
            user_id = recharge.user_id

            trans = get_transaction(txid)
            confirmations = trans['confirmations']

            if confirmations < settings.ETH_CONFIRMATIONS:
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

            cnt_confirm += 1

        self.stdout.write(self.style.SUCCESS('共确认 ' + str(cnt_confirm) + ' 条有效交易记录'))
        self.stdout.write(self.style.SUCCESS(''))
