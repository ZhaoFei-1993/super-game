from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from users.models import UserCoin, Coin, User
from console.models import Address


class Command(BaseCommand):
    help = "重新生成用户货币地址"

    @transaction.atomic()
    def handle(self, *args, **options):
        addresses = Address.objects.all().count()
        if addresses == 0:
            raise CommandError('地址库无数据')

        # 清空目前所有用户地址
        Address.objects.all().update(user=0)

        UserCoin.objects.all().update(address='')

        users = User.objects.filter(is_robot=False)
        if len(users) == 0:
            raise CommandError('当前无用户数据')

        # 获取货币数据
        coins = Coin.objects.filter(is_disabled=False)
        if len(coins) == 0:
            raise CommandError('未配置货币数据')

        if addresses < len(users):
            raise CommandError('地址库不足以分配当前所有用户')

        for user in users:
            self.stdout.write(self.style.SUCCESS('******正在分配用户ID=' + str(user.id) + '地址********'))
            btc_address = Address.objects.filter(user=0, coin_id=Coin.BTC).order_by('id').first()
            btc_address.user = user.id
            btc_address.save()
            self.stdout.write(self.style.SUCCESS('BTC=' + str(btc_address.address)))

            eth_address = Address.objects.filter(user=0, coin_id=Coin.ETH).order_by('id').first()
            eth_address.user = user.id
            eth_address.save()
            self.stdout.write(self.style.SUCCESS('ETH=' + str(eth_address.address)))

            for coin in coins:
                user_coins = UserCoin.objects.filter(user=user, coin=coin).count()
                if user_coins == 0:
                    user_coin = UserCoin()
                    user_coin.user = user
                    user_coin.coin = coin
                else:
                    user_coin = UserCoin.objects.get(user=user, coin=coin)

                # 是否ERC20协议代币
                if coin.is_eth_erc20:
                    user_coin.address = eth_address.address
                else:
                    user_coin.address = btc_address.address
                user_coin.save()

            self.stdout.write(self.style.SUCCESS('用户ID=' + str(user.id) + '分配地址成功'))
            self.stdout.write(self.style.SUCCESS(''))
