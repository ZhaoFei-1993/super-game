# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, Dividend, UserCoin, CoinDetail
from django.db.models import Sum
from django.db import transaction
from datetime import datetime, timedelta
from utils.functions import reversion_Decorator
from decimal import Decimal


class Command(BaseCommand):
    """
    GSG解锁
    """
    help = "GSG解锁"

    def handle(self, *args, **options):

        special_user = [1546, 3635]
        if special_user:
            self.special_handle(special_user)
            self.stdout.write(self.style.SUCCESS('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'))
        self.normal_handle()

    def normal_handle(self):
        """
        普通用户解锁
        :return:
        """
        self.stdout.write(self.style.SUCCESS('-----普通用户解锁操作开始-------'))
        now_time = datetime.now()
        coin_locks = UserCoinLock.objects.filter(is_free=0, is_divided=0, end_time__lte=now_time, total_amount=0)
        if coin_locks.exists():
            for x in coin_locks:
                dividend = Dividend.objects.filter(user_lock_id=x.id).values('user_lock__user_id', 'coin_id').annotate(
                    divide=Sum('divide')).order_by('coin_id')
                try:
                    gsg = UserCoin.objects.get(user_id=x.user_id, coin_id=6)
                except Exception:
                    raise CommandError('UserCoin表中找不到用户id为%i的GSG币' % x.user_id)
                gsg.balance += x.amount
                if dividend.exists():
                    for y in dividend:
                        user_id = y['user_lock__user_id']
                        try:
                            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=y['coin_id'])
                        except Exception:
                            raise CommandError('UserCoin表中找不到用户id为%i的coin_id= %i' % (user_id, y['coin_id']))
                        user_coin.balance += Decimal(str(y['divide']))
                        user_coin.save()
                        coin_detail = CoinDetail(user_id=user_id, coin_name=user_coin.coin.name, amount=Decimal(str(y['divide'])),rest=user_coin.balance, sources=CoinDetail.DEVIDEND)
                        coin_detail.save()
                x.is_free = 1
                x.is_divided = 1
                gsg.save()
                x.save()
                self.stdout.write(self.style.SUCCESS('普通用户id=%s解锁操作完成' % x.user_id))
        else:
            self.stdout.write(self.style.SUCCESS('普通用户当前无记录需要解锁'))
        self.stdout.write(self.style.SUCCESS('-----普通用户解锁操作结束-------'))

    def special_handle(self, users):
        """
        特别用户解锁操作
        :param users:
        :return:
        """
        self.stdout.write(self.style.SUCCESS('-----特别用户解锁操作开始-------'))
        now_time = datetime.now()
        coin_locks = UserCoinLock.objects.filter(user_id__in=users, is_free=0, is_divided=0, total_amount__gt=0)
        if coin_locks.exists():
            for x in coin_locks:
                delta = x.end_time - now_time
                if delta <= timedelta(days=150):
                    try:
                        gsg = UserCoin.objects.get(user_id=x.user_id, coin_id=6)
                    except Exception:
                        raise CommandError('UserCoin表中找不到用户id为%i的GSG币' % x.user_id)
                    if timedelta(days=120)<delta <= timedelta(days=150):
                        x.amount -= x.total_amount * Decimal(str(0.15))
                        gsg.balance += x.total_amount*Decimal(str(0.15))
                    elif timedelta(days=90)<delta <= timedelta(days=120):
                        x.amount -= x.total_amount * Decimal(str(0.15))
                        gsg.balance += x.total_amount * Decimal(str(0.15))
                    elif timedelta(days=60)<delta <= timedelta(days=90):
                        x.amount -= x.total_amount * Decimal(str(0.15))
                        gsg.balance += x.total_amount * Decimal(str(0.15))
                    elif timedelta(days=30)<delta <= timedelta(days=60):
                        x.amount -= x.total_amount * Decimal(str(0.15))
                        gsg.balance += x.total_amount * Decimal(str(0.15))
                    elif timedelta(days=0)<delta <= timedelta(days=30):
                        x.amount -= x.total_amount * Decimal(str(0.15))
                        gsg.balance += x.total_amount * Decimal(str(0.15))
                    else:
                        gsg.balance += Decimal(x.amount)
                        x.amount = Decimal(0)
                        dividend = Dividend.objects.filter(user_lock_id=x.id).values('coin_id').annotate(
                            divide=Sum('divide')).order_by('coin_id')
                        if dividend.exists():
                            for y in dividend:
                                try:
                                    user_coin = UserCoin.objects.get(user_id=x.user_id, coin_id=y['coin_id'])
                                except Exception:
                                    raise CommandError('UserCoin表中找不到用户id为%i的coin_id= %i' % (x.user_id, y['coin_id']))
                                user_coin.balance += Decimal(str(y['divide']))
                                user_coin.save()
                                coin_detail = CoinDetail(user_id=x.user_id, coin_name=user_coin.coin.name, amount=Decimal(str(y['divide'])),rest=user_coin.balance, sources=CoinDetail.DEVIDEND)
                                coin_detail.save()
                        x.is_free = 1
                        x.is_divided = 1
                    gsg.save()
                    x.save()
                    self.stdout.write(self.style.SUCCESS('特殊用户user_id=%s解锁操作完成' % x.user_id))
        else:
            self.stdout.write(self.style.SUCCESS('特殊用户当前无记录需要解锁'))

        self.stdout.write(self.style.SUCCESS('-----特殊用户解锁操作结束----'))