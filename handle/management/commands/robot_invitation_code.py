# -*- coding: utf-8 -*-

from django.db.models import Q
from django.core.management.base import BaseCommand
from users.models import CoinGiveRecords, UserCoin


class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
        give_len = CoinGiveRecords.objects.filter(~Q(lock_coin=0)).count()
        give_len_two = CoinGiveRecords.objects.filter(lock_coin=0).count()
        give_len_one = CoinGiveRecords.objects.filter(lock_coin__lt=0).count()
        print("give_len=============================", give_len)
        print("give_len_two=============================", give_len_two)
        print("give_len_one=============================", give_len_one)
        give_usdt = CoinGiveRecords.objects.filter(~Q(lock_coin=0))
        i = 1
        for give in give_usdt:
            user_usdt = UserCoin.objects.get(user_id=give.user.pk, coin_id=9)
            if user_usdt.balance < give.lock_coin:
                user_usdt.balance = 0
            else:
                user_usdt.balance -= give.lock_coin
            user_usdt.save()
            give.lock_coin = 0
            give.save()
            print("i=================================", i, "====================================", user_usdt.user.pk)
            i += 1
