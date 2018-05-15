from django.core.management.base import BaseCommand
from django.db.models import Q

from users.models import UserCoin, Coin

from console.models import Address


class Command(BaseCommand):
    help = "Test"

    def handle(self, *args, **options):
        # UserCoin.objects.filter(~Q(address='')).update(address='')
        UserCoin.objects.all().update(address='')
        coins = Coin.objects.filter(~Q(pk=8))
        for coin in coins:
            # user_coin_number = UserCoin.objects.filter(~Q(address=''), coin_id=coin.pk).count()
            user_coin_number = UserCoin.objects.filter(coin_id=coin.pk).count()
            address_list = Address.objects.filter(coin_id=coin.pk, user="")[:int(user_coin_number)]
            # user_coin_list = UserCoin.objects.filter(~Q(address=''), coin_id=coin.pk)
            user_coin_list = UserCoin.objects.filter(coin_id=coin.pk)
            i = 0
            for user_coin in user_coin_list:
                user_coin.address = address_list[i].address
                user_coin.save()
                address_list[i].user = user_coin.user.pk
                address_list[i].save()
                print("来来来，老夫来给你一个坑钱地址====================", i)
                i += 1
