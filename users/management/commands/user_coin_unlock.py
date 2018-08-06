# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime
from users.models import UserCoinLock
from utils.cache import get_cache, set_cache
import dateparser


class Command(BaseCommand):
    """
    锁定解锁
    查找出最新一条即将到期的数据（如：2018-08-08 11:11:11），存入缓存中，下次脚本运行只读取缓存记录，
    判断是否过期（需要考虑用户延长的情况）将该过期数据对应数据库记录改为释放状态，然后再往缓存中记录最新到期记录
    """
    help = "锁定解锁"

    key_unlock = 'user_coin_unlock_datetime'

    def set_expire_lock_cache(self):
        """
        从数据库中获取即将到期的锁定记录，并写入缓存中
        :return:
        """
        user_coin_lock = UserCoinLock.objects.filter(is_free=False).order_by('end_time').first()
        set_cache(self.key_unlock, str(user_coin_lock.id) + ',' + str(user_coin_lock.end_time))

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('-----锁定解锁脚本开始运行-----'))
        # 从缓存中获取即将到期的数据
        cache_lock_datetime = get_cache(self.key_unlock)

        lock_id = 0
        if cache_lock_datetime is not None:
            user_lock_id, lock_end_time = cache_lock_datetime.split(',')
            if dateparser.parse(lock_end_time) <= datetime.now():
                # 判断用户是否有延期操作，再从DB中取一次来判断
                user_coin_lock = UserCoinLock.objects.get(pk=user_lock_id)
                if user_coin_lock.end_time <= datetime.now():
                    lock_id = user_lock_id
                    user_coin_lock.is_free = True
                    user_coin_lock.save()

                    self.set_expire_lock_cache()
                else:
                    self.set_expire_lock_cache()
        else:
            user_coin_lock = UserCoinLock.objects.filter(is_free=False).order_by('end_time').first()

            # 判断是否过期，若是，则解除锁定状态
            if user_coin_lock.end_time <= datetime.now():
                lock_id = user_coin_lock.id
                user_coin_lock.is_free = True
                user_coin_lock.save()

            # 获取下一条锁定记录，写入缓存中
            self.set_expire_lock_cache()

        if lock_id == 0:
            self.stdout.write(self.style.SUCCESS('当前无满足解锁条件的记录'))
        else:
            self.stdout.write(self.style.SUCCESS('已解锁ID=' + str(lock_id) + '的用户锁定记录'))
