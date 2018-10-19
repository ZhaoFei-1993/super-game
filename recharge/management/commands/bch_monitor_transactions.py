# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from base.app import BaseView
from base.eth import Wallet
from local_settings import BCH_WALLET_API_URL
from users.models import UserRecharge, Coin, UserCoin, CoinDetail
from decimal import Decimal
from utils.cache import set_cache, get_cache


class Command(BaseCommand, BaseView):
    help = "Bitcoin Cash交易数据监控"
    cacheKey = 'key_bch_block_height'

    @staticmethod
    def get_transaction(transaction_hash):
        """
        根据transactionHash获取交易数据
        :param transaction_hash:
        :return:
        """
        eth_wallet = Wallet()
        json_data = eth_wallet.get(url=BCH_WALLET_API_URL + 'v1/bch/block/tx/' + str(transaction_hash))
        if json_data['code'] > 0:
            raise CommandError(json_data['message'] + ' tx = ' + transaction_hash)

        return json_data['data']

    def handle(self, *args, **options):
        bch_transactions = get_cache('key_bch_transactions')
        if bch_transactions is None or bch_transactions == 0:
            raise CommandError('未获取到充值')

        confirm_number = 1  # 有效交易确认数

        # 获取所有用户ETH交易hash，只获取交易确认数小于指定值的数据
        user_recharges = UserRecharge.objects.filter(coin_id=Coin.BCH, confirmations__lt=confirm_number)
        if len(user_recharges) == 0:
            set_cache('key_bch_transactions', 0)
            raise CommandError('无充值信息')

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(user_recharges)) + '条充值记录'))

        cnt_confirm = 0
        for recharge in user_recharges:
            txid = recharge.txid
            user_id = recharge.user_id
            coin = Coin.objects.get_one(pk=Coin.BCH)

            transaction = self.get_transaction(txid)
            confirmations = transaction['confirmations']

            if confirmations < confirm_number:
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

            self.stdout.write(self.style.SUCCESS('确认一笔 ' + str(coin.name) + ' 充值，TXID=' + txid))

            cnt_confirm += 1

        self.stdout.write(self.style.SUCCESS('共确认 ' + str(cnt_confirm) + ' 条有效充值记录'))
        self.stdout.write(self.style.SUCCESS(''))
