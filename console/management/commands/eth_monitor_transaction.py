# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from users.models import UserRecharge, Coin, UserCoin, CoinDetail
from decimal import Decimal
from base.function import curl_get
from console.consumers.eth_monitor import get_api_url


def get_transaction(transaction_hash):
    """
    根据transactionHash获取交易数据
    :param transaction_hash:
    :return:
    """
    response = curl_get(url=get_api_url('eth_getTransactionByHash&txhash=' + transaction_hash))
    if 'error' in response:
        raise CommandError('获取交易信息失败：tx=' + transaction_hash)

    return response['result']


class Command(BaseCommand):
    help = "ETH交易确认监视器"

    @staticmethod
    def get_block_height():
        """
        获取区块链上最大节点高度
        :return:
        """
        try:
            response = curl_get(url=get_api_url('eth_blockNumber'))
            block_height = int(response['result'], 0)
        except Exception:
            raise CommandError('获取区块链最新节点高度失败')

        return block_height

    @transaction.atomic()
    def handle(self, *args, **options):
        # 获取所有用户ETH交易hash，只获取交易确认数小于指定值的数据
        eth_coin_ids = [1, 2, 4]
        user_recharges = UserRecharge.objects.filter(coin_id__in=eth_coin_ids, confirmations__lt=settings.ETH_CONFIRMATIONS)
        if len(user_recharges) == 0:
            raise CommandError('暂无充值信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_recharges)) + '条用户ETH交易信息'))

        # 获取当前区块链最大高度
        current_block_height = self.get_block_height()

        cnt_confirm = 0
        for recharge in user_recharges:
            txid = recharge.txid
            user_id = recharge.user_id
            coin_id = recharge.coin_id

            coin = Coin.objects.get(pk=coin_id)

            trans = get_transaction(txid)
            confirmations = current_block_height - int(trans['blockNumber'], 0)

            if confirmations < settings.ETH_CONFIRMATIONS:
                self.stdout.write(self.style.SUCCESS(txid + ' 确认数未达标'))
                continue

            recharge.confirmations = confirmations
            recharge.save()

            # 首次充值获得奖励
            UserRecharge.objects.first_price(user_id)

            # 用户充值成功
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin.id)
            user_coin.balance += Decimal(str(recharge.amount))
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
