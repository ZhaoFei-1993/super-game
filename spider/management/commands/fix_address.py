# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserCoin, User, Coin
from django.db.models import Q
from console.models import Address


class Command(BaseCommand):
    help = "fix address"

    def handle(self, *args, **options):
        i = 1
        for user_coin in UserCoin.objects.all():
            if Address.objects.filter(user=0, address=user_coin.address).exists():
                print('====================>', i)
                i += 1
                address = Address.objects.filter(user=0, address=user_coin.address).first()
                address.user = user_coin.user_id
                address.save()
