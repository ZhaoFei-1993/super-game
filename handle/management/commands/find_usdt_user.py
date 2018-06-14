# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import CoinGiveRecords, UserCoin
from quiz.models import Record


class Command(BaseCommand):
    help = "寻找不同步usdt用户"

    def handle(self, *args, **options):
        # quiz_list = []
        for coin_give_records in CoinGiveRecords.objects.filter(is_recharge_lock=False, user__is_block=False,
                                                                user__is_robot=False):
            user_coin = UserCoin.objects.get(coin_id=coin_give_records.coin_give.coin.id, user_id=coin_give_records.user.id)
            if float(user_coin.balance) == float(coin_give_records.lock_coin):
                pass
            else:
                print("normalize_fraction(user_coin.balance, 2)=========================", float(user_coin.balance))
                print("coin_give_records.coin_give.coin.id=========================", coin_give_records.coin_give.coin.id)
                print("coin_give_records.user.id=========================", coin_give_records.user.id)
                print("user_coin.user.id=========================", user_coin.user.id)
                print("normalize_fraction(coin_give_records.lock_coin, 2)=========================",
                      float(coin_give_records.lock_coin))
                print(coin_give_records.user.id, ',')

        # print('-----------------------------------------------------------------------')
        #
        # for coin_give_records in CoinGiveRecords.objects.filter(is_recharge_lock=False, user__is_block=False,
        #                                                         user__is_robot=False):
        #     for record in Record.objects.filter(user=coin_give_records.user, roomquiz_id=6, source=str(Record.GIVE)):
        #         if record.quiz_id not in quiz_list:
        #             quiz_list.append(record.quiz_id)
        #     if coin_give_records.lock_coin >= 60 and len(quiz_list) >= 6:
        #         print(coin_give_records.user.id, ',')
