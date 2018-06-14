# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import CoinGiveRecords, UserCoin
from quiz.models import Record
from utils.functions import normalize_fraction


class Command(BaseCommand):
    help = "寻找不同步usdt用户"

    def handle(self, *args, **options):
        quiz_list = []
        for coin_give_records in CoinGiveRecords.objects.filter(is_recharge_lock=False, user__is_block=False,
                                                                user__is_robot=False):
            user_coin = UserCoin.objects.get(coin=coin_give_records.coin_give.coin, user=coin_give_records.user)
            print("user_coin=========================================", user_coin)
            if normalize_fraction(user_coin.balance, 2) != normalize_fraction(coin_give_records.lock_coin, 2):
                print(coin_give_records.user.id, ',')

        print('-----------------------------------------------------------------------')

        for coin_give_records in CoinGiveRecords.objects.filter(is_recharge_lock=False, user__is_block=False,
                                                                user__is_robot=False):
            for record in Record.objects.filter(user=coin_give_records.user, roomquiz_id=6, source=str(Record.GIVE)):
                if record.quiz_id not in quiz_list:
                    quiz_list.append(record.quiz_id)
            if coin_give_records.lock_coin >= 60 and len(quiz_list) >= 6:
                print(coin_give_records.user.id, ',')
