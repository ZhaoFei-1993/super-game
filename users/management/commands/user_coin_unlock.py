# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import datetime, timedelta
from users.models import UserCoinLock, UserMessage
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
    def pre_release_unlock_message(end_time, user_id):
        """
        提前xxx小时解锁提醒
        :param  end_time    结束时间
        :param  user_id     用户ID
        :return:
        """
        if datetime.now() + timedelta(seconds=settings.GSG_UNLOCK_PREACT_TIME) < end_time:
            return True

        hours = settings.GSG_UNLOCK_PREACT_TIME / 3600

        # TODO: 判断是否已经发过提醒信息

        # 发送信息
        user_message = UserMessage()
        user_message.status = 0
        user_message.content = '亲爱的用户您好，你锁定的XXX GSG ' + str(hours) + '小时后到期，如需延长参与锁定即分红时间，请到个人钱包进行操作。'
        user_message.title = 'GSG锁定即将到期提醒'
        user_message.user_id = user_id
        user_message.message_id = 6
        user_message.save()

    def release_user_coin_lock(self, user_lock_id):
        """
        释放用户锁定
        :param user_lock_id
        :return:
        """
        lock_id = 0

        user_coin_lock = UserCoinLock.objects.get(pk=user_lock_id)

        if user_coin_lock.end_time <= datetime.now():
            lock_id = user_lock_id
            user_coin_lock.is_free = True
            user_coin_lock.save()

            amount = str(user_coin_lock.amount)

            # 发送解锁信息
            user_message = UserMessage()
            user_message.status = 0
            user_message.content = '亲爱的用户您好，你锁定的' + amount + ' GSG 已到期，重新参与锁定即分红活动，请到个人钱包进行操作。'
            user_message.title = 'GSG锁定到期提醒'
            user_message.user_id = user_coin_lock.user_id
            user_message.message_id = 6
            user_message.save()

            self.set_expire_lock_cache()

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
            else:
                self.pre_release_unlock_message(lock_end_time, user_id)
        else:
            user_coin_lock = UserCoinLock.objects.filter(is_free=False).order_by('end_time').first()

            # 判断是否过期，若是，则解除锁定状态
            lock_id = self.release_user_coin_lock(user_coin_lock.id)

        if lock_id == 0:
            self.stdout.write(self.style.SUCCESS('当前无满足解锁条件的记录'))
        else:
            self.stdout.write(self.style.SUCCESS('已解锁ID=' + str(lock_id) + '的用户锁定记录'))
