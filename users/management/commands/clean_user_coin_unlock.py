# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users.models import UserCoinLock, UserMessage, UserCoin, Coin


class Command(BaseCommand):
    """
    清除当前所有用户锁定记录
    """
    help = "清除当前所有用户锁定记录"

    @transaction.atomic()
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('-----清除当前所有用户锁定记录脚本开始运行-----'))
        user_coin_locks = UserCoinLock.objects.all()
        if len(user_coin_locks) == 0:
            raise CommandError('No user coin lock record')

        self.stdout.write(self.style.SUCCESS('共查询到' + str(len(user_coin_locks)) + '条锁定记录'))

        for user_coin_lock in user_coin_locks:
            user_coin_lock.is_free = True
            user_coin_lock.save()

            # 返回用户余额
            user_coin = UserCoin.objects.get(user_id=user_coin_lock.user_id, coin_id=Coin.GSG)
            user_coin.balance += user_coin_lock.amount
            user_coin.save()

            amount = str(float(user_coin_lock.amount))

            # 发送用户说明信息
            user_message = UserMessage()
            user_message.status = 0
            user_message.content = '尊敬的用户你好，由于锁定分红功能还在内测完善中，你锁定的' + amount + ' GSG已解除锁定并返还到你的个人钱包，请查收！'
            user_message.title = 'GSG锁定解除通知'
            user_message.user_id = user_coin_lock.user_id
            user_message.message_id = 6
            user_message.save()

        self.stdout.write(self.style.SUCCESS('解锁完成'))
