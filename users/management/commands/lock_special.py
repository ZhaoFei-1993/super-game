from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, User, CoinDetail, UserCoin
from datetime import timedelta
from utils.functions import reversion_Decorator
from decimal import Decimal


class Command(BaseCommand):
    """
    GSG解锁
    """
    help = "GSG锁定"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('---------锁定脚本开始运行---------'))
        special_user = []#存入格式类似[（电话号码， 锁定金额）,(..)]
        if special_user:
            for x in special_user:
                if len(x)==2:
                    coin_lock = UserCoinLock()
                    try:
                        user = User.objects.get(username=str(x[0]))
                    except Exception:
                        raise CommandError('号码为%s用户不存在, 需要先注册用户' % str(x[0]))
                    try:
                        gsg = UserCoin.objects.get(user_id=user.id, coin_id=6)
                    except Exception:
                        raise CommandError('UserCoin表中找不到用户%s的GSG币对应id' % user.telephone)
                    coin_lock.user=user
                    coin_lock.amount = Decimal(str(x[1]))
                    coin_lock.coin_lock_id = 2
                    coin_lock.total_amount= Decimal(str(x[1]))
                    coin_lock.save()
                    coin_lock.end_time=coin_lock.created_at+timedelta(days=180)
                    coin_lock.save()
                    coin_detail = CoinDetail(user=user, coin_name=gsg.coin.name, amount=coin_lock.amount,rest=gsg.balance, sources=CoinDetail.LOCK)
                    coin_detail.save()
                    self.stdout.write(self.style.SUCCESS('手机号码为%s的用户锁定完成' % user.telephone))
                else:
                    raise CommandError("列表存入格式不正确， 格式如：[(电话号码, 锁定金额),(...)]")
        self.stdout.write(self.style.SUCCESS('---------锁定脚本运行结束---------'))
