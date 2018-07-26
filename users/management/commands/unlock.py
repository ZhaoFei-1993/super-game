# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, Dividend, UserCoin, CoinDetail
from django.db.models import Sum
from django.db import transaction
from datetime import datetime


class Command(BaseCommand):
    """
    GSG解锁
    """
    help = "GSG解锁"

    @transaction.atomic()
    def handle(self, *args, **options):
        now_time = datetime.now()
        coin_locks = UserCoinLock.objects.filter(is_free=0, is_divided=0, end_time__lte=now_time)
        if coin_locks.exists():
            for x in coin_locks:
                dividend = Dividend.objects.filter(user_lock_id=x.id).values('user_lock__user_id', 'coin_id').annotate(
                    divide=Sum('divide')).order_by('coin_id')
                if dividend.exists():
                    for y in dividend:
                        user_id = y['user_lock__user_id']
                        try:
                            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=y['coin_id'])
                        except Exception:
                            raise CommandError('UserCoin表中找不到用户id为%i的coin_id= %i' % (user_id, y['coin_id']))
                        user_coin.balance += y['divide']
                        user_coin.save()
                        coin_detail = CoinDetail(user_id=user_id, coin_name=user_coin.coin.name, amount=y['divide'],
                                                 rest=user_coin.balance, sources=CoinDetail.DEVIDEND)
                        coin_detail.save()
                x.is_free = 1
                x.is_divided = 1
                x.save()
            self.stdout.write(self.style.SUCCESS('解锁操作完成'))
        else:
            self.stdout.write(self.style.SUCCESS('当前无记录需要解锁'))
