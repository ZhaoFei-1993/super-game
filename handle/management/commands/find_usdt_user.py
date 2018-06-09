# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import CoinGiveRecords, UserCoin


class Command(BaseCommand):
    help = "寻找不同步usdt用户"

    def handle(self, *args, **options):
        for coin_give_records in CoinGiveRecords.objects.all():
            user_coin = UserCoin.objects.filter(coin=coin_give_records.coin_give.coin,
                                                user=coin_give_records.user).first()
            if float(user_coin.balance) < float(coin_give_records.lock_coin):
                print(coin_give_records.user.id, ',')
