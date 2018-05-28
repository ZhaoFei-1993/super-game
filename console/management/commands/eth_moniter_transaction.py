# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from users.models import UserRecharge, Coin
from base.eth import *


def get_transaction(transaction_hash):
    """
    根据transactionHash获取交易数据
    :param transaction_hash:
    :return:
    """
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/transaction/' + transaction_hash)
    print('json_data = ', json_data)
    if json_data['code'] > 0:
        raise CommandError(json_data['message'] + ' tx = ' + transaction_hash)

    return json_data


class Command(BaseCommand):
    help = "ETH交易信息监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取所有用户ETH交易hash，只获取交易确认数小于指定值的数据
        user_recharges = UserRecharge.objects.filter(coin_id=Coin.ETH, confirmations__lt=settings.ETH_CONFIRMATIONS)
        if len(user_recharges) == 0:
            raise CommandError('无交易信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_recharges)) + '条用户ETH交易信息'))

        cnt_confirm = 0
        for recharge in user_recharges:
            txid = recharge.txid
            user_id = recharge.user_id

            trans = get_transaction(txid)
            if trans['confirmations'] < settings.ETH_CONFIRMATIONS:
                continue

            recharge.confirmations = trans['confirmations']
            recharge.save()

            # 首次充值获得奖励
            UserRecharge.objects.first_price(user_id)

            cnt_confirm += 1

        self.stdout.write(self.style.SUCCESS('共确认 ' + str(cnt_confirm) + ' 条有效交易记录'))
        self.stdout.write(self.style.SUCCESS(''))
