# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserCoin, User, Coin
from django.db.models import Q
from console.models import Address


class Command(BaseCommand):
    help = "更换用户ETH地址"

    def handle(self, *args, **options):
        for user_coin in UserCoin.objects.filter(~Q(address=''), coin__is_eth_erc20=False):
            i = 1
            user_address = user_coin.address
            if Address.objects.filter(address=user_address).first().coin.is_eth_erc20 is True:
                print('=========================>', i)
                i += 1
                address = Address.objects.filter(address=user_address).first()
                address.user = 0
                address.save()

                user_usdt = UserCoin.objects.filter(user_id=user_coin.user_id, coin__name='USDT').first()
                new_address = Address.objects.filter(user=0, coin__id=Coin.BTC).first().address
                user_coin.address = new_address
                user_usdt.address = new_address
                user_coin.save()
                user_usdt.save()
