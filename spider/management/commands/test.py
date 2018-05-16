from django.core.management.base import BaseCommand
from django.db.models import Q

from users.models import UserCoin, Coin

from console.models import Address


class Command(BaseCommand):
    help = "Test"

    def handle(self, *args, **options):
        # UserCoin.objects.filter(~Q(address='')).update(address='')    # 1
        UserCoin.objects.all().update(address='')
        Address.objects.all().update(user='')
        # Address.objects.filter(~Q(user='')).update(user='')        # 1
        coins = Coin.objects.filter(~Q(pk=8))
        # coins = Coin.objects.all()
        for coin in coins:
            # user_coin_number = UserCoin.objects.filter(~Q(address=''), coin_id=coin.pk).count()           # 1
            # if user_coin_number == 0:          # 1
            #     continue               # 1
            user_coin_number = UserCoin.objects.filter(coin_id=coin.pk).count()
            address_list = Address.objects.filter(coin_id=coin.pk, user="")[:int(user_coin_number)]
            # address_list = Address.objects.filter(~Q(user=""), coin_id=coin.pk,)[:int(user_coin_number)]           # 1
            # user_coin_list = UserCoin.objects.filter(~Q(address=''), coin_id=coin.pk)             # 1
            user_coin_list = UserCoin.objects.filter(coin_id=coin.pk)
            i = 0
            for user_coin in user_coin_list:
                print("来来来，老夫来给你一个坑钱地址====================", i)
                user_coin.address = address_list[i].address
                user_coin.save()
                address_info = Address.objects.get(address=address_list[i].address, user='')
                address_info.user = str(user_coin.user.pk)
                address_info.save()
                i += 1
