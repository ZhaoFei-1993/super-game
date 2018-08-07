# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime
from users.models import UserCoinLock, UserMessage, PreReleaseUnlockMessageLog, UserCoin, CoinDetail, Coin
from utils.cache import get_cache, set_cache
import dateparser
from django.conf import settings


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

        cache_val = str(user_coin_lock.id) + ',' + str(user_coin_lock.user_id) + ',' + str(user_coin_lock.end_time)
        set_cache(self.key_unlock, cache_val)

    @staticmethod
    def pre_release_unlock_message(user_coin_lock):
        """
        提前xxx小时解锁提醒
        :param  user_coin_lock
        :return:
        """
        time_diff = (user_coin_lock.end_time - datetime.now()).seconds
        if time_diff > settings.GSG_UNLOCK_PREACT_TIME:
            return True

        hours = int(time_diff / 3600)

        # 判断是否已经发送过提醒信息
        pre_release_unlock_message = PreReleaseUnlockMessageLog.objects.filter(user_coin_lock_id=user_coin_lock.id, is_delete=False).count()
        if pre_release_unlock_message > 0:
            return True

        # 发送信息
        user_message = UserMessage()
        user_message.status = 0
        user_message.content = '亲爱的用户您好，你锁定的' + str(int(user_coin_lock.amount)) + ' GSG ' + str(hours) + '小时后到期，如需延长参与锁定即分红时间，请到个人钱包进行操作。'
        user_message.title = 'GSG锁定即将到期提醒'
        user_message.user_id = user_coin_lock.user_id
        user_message.message_id = 6
        user_message.save()

        pre_release_unlock_message_log = PreReleaseUnlockMessageLog()
        pre_release_unlock_message_log.user_id = user_coin_lock.user_id
        pre_release_unlock_message_log.user_coin_lock_id = user_coin_lock.id
        pre_release_unlock_message_log.user_message_id = user_message.id
        pre_release_unlock_message_log.save()
        print('ID=' + str(user_coin_lock.user_id) + ' 即将自动解锁提醒')

    def release_user_coin_lock(self, user_lock_id=0):
        """
        释放用户锁定
        :param user_lock_id
        :return:
        """
        lock_id = 0

        if user_lock_id == 0:
            user_coin_lock = UserCoinLock.objects.filter(is_free=False).order_by('end_time').first()
        else:
            user_coin_lock = UserCoinLock.objects.get(pk=user_lock_id)

        if user_coin_lock.end_time <= datetime.now():
            lock_id = user_coin_lock.id
            user_coin_lock.is_free = True
            user_coin_lock.save()

            amount = str(int(user_coin_lock.amount))
            user_id = user_coin_lock.user_id

            # 发送解锁信息
            user_message = UserMessage()
            user_message.status = 0
            user_message.content = '亲爱的用户您好，你锁定的' + amount + ' GSG 已到期，重新参与锁定即分红活动，请到个人钱包进行操作。'
            user_message.title = 'GSG锁定到期提醒'
            user_message.user_id = user_id
            user_message.message_id = 6
            user_message.save()

            # 将余额返回给用户
            user_coin = UserCoin.objects.select_for_update().get(user_id=user_id, coin_id=Coin.GSG)
            user_coin.balance += user_coin_lock.amount
            user_coin.save()

            # 写入用户余额变更记录表
            coin_detail = CoinDetail()
            coin_detail.user_id = user_id
            coin_detail.coin_name = 'GSG'
            coin_detail.amount = str(user_coin_lock.amount)
            coin_detail.rest = user_coin.balance
            coin_detail.sources = CoinDetail.UNLOCK
            coin_detail.save()
        else:
            self.pre_release_unlock_message(user_coin_lock)

        return lock_id

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('-----锁定解锁脚本开始运行-----'))
        # 从缓存中获取即将到期的数据
        cache_lock_datetime = get_cache(self.key_unlock)

        lock_id = 0
        if cache_lock_datetime is not None:
            user_lock_id, user_id, lock_end_time = cache_lock_datetime.split(',')
            lock_end_time = dateparser.parse(lock_end_time)

            if lock_end_time <= datetime.now():
                # 判断用户是否有延期操作，再从DB中取一次来判断
                lock_id = self.release_user_coin_lock(user_lock_id)

                self.set_expire_lock_cache()
            else:
                user_coin_lock = UserCoinLock.objects.get(pk=user_lock_id)
                self.pre_release_unlock_message(user_coin_lock)
        else:
            # 若缓存中无数据，则在DB中读取
            lock_id = self.release_user_coin_lock()

            self.set_expire_lock_cache()

        if lock_id == 0:
            self.stdout.write(self.style.SUCCESS('当前无满足解锁条件的记录'))
        else:
            self.stdout.write(self.style.SUCCESS('已解锁ID=' + str(lock_id) + '的用户锁定记录'))
