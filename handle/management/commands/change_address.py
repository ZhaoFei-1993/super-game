# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserCoin, User, Coin
from django.db.models import Q
from console.models import Address


class Command(BaseCommand):
    help = "更换用户ETH地址"

    def handle(self, *args, **options):
        i = 1
        for user_coin in UserCoin.objects.filter(~Q(address=''), coin__is_eth_erc20=False):
            user_address = user_coin.address
            if Address.objects.filter(address=user_address).first().coin.is_eth_erc20 is True:
                address = Address.objects.filter(address=user_address).first()
                address.user = 0
                address.save()

                user_usdt = UserCoin.objects.filter(user_id=user_coin.user_id, coin__name='USDT').first()
                new_address = Address.objects.filter(user=0, coin__id=Coin.BTC).first()
                user_coin.address = new_address.address
                user_usdt.address = new_address.address
                new_address.user = user_coin.user_id
                new_address.save()
                user_coin.save()
                user_usdt.save()

                print('=========================> ', i, '=================address=====> ', new_address.address)
                i += 1
