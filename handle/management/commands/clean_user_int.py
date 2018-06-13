# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, UserCoin, Coin


class Command(BaseCommand):
    help = "被封禁用户int清零"

    def handle(self, *args, **options):
        int_coin = Coin.objects.get(name='INT')
        for block_user in User.objects.filter(is_block=True, is_robot=False):
            block_user_int_coin = UserCoin.objects.get(user=block_user, coin=int_coin)
            block_user_int_coin.balance = 0
            block_user_int_coin.save()