from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, User, CoinDetail, UserCoin, Coin
from datetime import datetime, timedelta
from django.db import transaction


class Command(BaseCommand):
    """
    GSG特别用户锁定
    """
    help = "GSG锁定"

    def add_arguments(self, parser):
        parser.add_argument('telephone', type=str)
        parser.add_argument('amount', type=int)

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('---------锁定脚本开始运行---------'))
        telephone = options['telephone']
        amount = options['amount']

        # 判断用户telephone是否有效
        try:
            user = User.objects.get(username=telephone)
        except User.DoesNotExist:
            raise CommandError('电话号码未注册')

        # 判断用户是否有锁定记录
        user_coin_lock = UserCoinLock.objects.filter(user_id=user.id, is_free=False).count()
        if user_coin_lock > 0:
            raise CommandError('该用户已有锁定记录')

        # 判断user_coin是否有GSG记录
        user_coin = UserCoin.objects.filter(user_id=user.id, coin_id=Coin.GSG).count()
        if user_coin == 0:
            user_coin_eth = UserCoin.objects.get(user_id=user.id, coin_id=Coin.ETH)

            user_coin_new = UserCoin()
            user_coin_new.user_id = user.id
            user_coin_new.coin_id = Coin.GSG
            user_coin_new.balance = 0
            user_coin_new.address = user_coin_eth.address
            user_coin_new.save()

        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=Coin.GSG)

        # 插入锁定记录
        created_at = datetime.now()
        user_coin_lock = UserCoinLock()
        user_coin_lock.user_id = user.id
        user_coin_lock.coin_lock_id = 4
        user_coin_lock.amount = amount
        user_coin_lock.total_amount = amount
        user_coin_lock.end_time = created_at + timedelta(180)
        user_coin_lock.is_free = False
        user_coin_lock.is_divided = False
        user_coin_lock.created_at = created_at
        user_coin_lock.save()

        # 插入余额变更记录表
        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = 'GSG'
        coin_detail.amount = amount
        coin_detail.rest = user_coin.balance
        coin_detail.sources = CoinDetail.LOCK
        coin_detail.save()

        self.stdout.write(self.style.SUCCESS('手机号码为%s的用户锁定个%sGSG' % (telephone, str(amount))))
