from django.db import models
from users.models import Coin, UserCoin


class AddressManager(models.Manager):
    """
    地址库数据操作
    """
    @staticmethod
    def initial(user_id, user_coins=None):
        """
        初始数据
        :param  user_id 用户ID
        :param  user_coins  用户货币数据
        :return:
        """
        all_coins = Coin.objects.get_all()
        if len(all_coins) == 0:
            return True

        coins = []
        obj_coin = {}
        for coin in all_coins:
            if coin.is_disabled is True:
                continue
            coins.append(coin)
            obj_coin[coin.id] = coin

        # 启用的货币ID
        coin_ids = [coin.id for coin in coins]

        eth_address = None
        btc_address = None
        if user_coins is None:
            user_coins = UserCoin.objects.filter(user_id=user_id)
        if len(user_coins) > 0:
            for user_coin in user_coins:
                if user_coin.coin_id == Coin.ETH:
                    eth_address = user_coin.address
                if user_coin.coin_id == Coin.BTC:
                    btc_address = user_coin.address

                # 获取到地址跳出循环
                if eth_address is not None and btc_address is not None:
                    break

        # 用户当前已分配的货币ID
        user_coin_ids = [coin.coin_id for coin in user_coins]

        # 计算出用户缺少的coin_id的数据
        arr_coins = list(set(coin_ids).difference(set(user_coin_ids)))
        if len(arr_coins) == 0:
            return True

        for coin_id in arr_coins:
            coin = obj_coin[coin_id]

            # EOS
            if coin_id in [8]:
                coin_address = ''
            else:
                # ETH及代币
                if coin.is_eth_erc20:
                    # 判断用户是否有地址，若有，则直接用地址，无则从地址库中拿出来
                    if eth_address is None:
                        address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.ETH).first()
                        address.user = user_id
                        address.save()
                        coin_address = address.address
                        eth_address = coin_address
                    else:
                        coin_address = eth_address
                # BTC、USDT、BCH
                else:
                    if btc_address is None:
                        address = Address.objects.select_for_update().filter(user=0, coin_id=Coin.BTC).first()
                        address.user = user_id
                        address.save()
                        coin_address = address.address
                        btc_address = coin_address
                    else:
                        coin_address = btc_address

            user_coin = UserCoin()
            user_coin.coin_id = coin_id
            user_coin.user_id = user_id
            user_coin.balance = 0
            user_coin.address = coin_address
            user_coin.save()


class Address(models.Model):
    coin = models.ForeignKey(Coin, on_delete=models.CASCADE)
    address = models.CharField(verbose_name='地址', max_length=128)
    passphrase = models.CharField(verbose_name='密串', max_length=128)
    # user = models.CharField(verbose_name="用户ID", max_length=128, default="")
    user = models.IntegerField(verbose_name="用户ID", default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    objects = AddressManager()

    class Meta:
        ordering = ['-id']
        verbose_name = verbose_name_plural = "充值地址"
