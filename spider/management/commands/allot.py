# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserCoin, CoinDetail, Coin, UserMessage, User
from chat.models import Club
from decimal import Decimal


class Command(BaseCommand):
    help = "发配HAND"

    def handle(self, *args, **options):
        club = Club.objects.get(pk=4)
        coin = Coin.objects.get(pk=club.coin_id)
        for user in User.objects.all():
            try:
                user_coin = UserCoin.objects.get(user_id=user.id, coin=coin)
            except UserCoin.DoesNotExist:
                user_coin = UserCoin()
            user_coin.coin_id = club.coin_id
            user_coin.user_id = user.id
            user_coin.balance = Decimal(user_coin.balance) + Decimal(8000)
            user_coin.save()

            # 用户资金明细表
            coin_detail = CoinDetail()
            coin_detail.user_id = user.id
            coin_detail.coin_name = coin.name
            coin_detail.amount = Decimal(8000)
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.OTHER
            coin_detail.save()

            # 发送信息
            u_mes = UserMessage()
            u_mes.status = 0
            u_mes.user_id = user.id
            u_mes.message_id = 8  # 私人信息
            u_mes.save()
