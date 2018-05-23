# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from users.models import User, UserCoin
from quiz.models import Record
from django.db import transaction


class Command(BaseCommand):
    """
    删除旧机器人数据
    """
    help = "删除旧机器人数据"

    @transaction.atomic()
    def handle(self, *args, **options):
        user_coins = UserCoin.objects.all()

        user_ids = []
        users = User.objects.all()
        for user in users:
            user_ids.append(user.id)

        delete_user_ids = []
        for user_coin in user_coins:
            if user_coin.user_id not in user_ids:
                delete_user_ids.append(user_coin.user_id)

        self.stdout.write(self.style.SUCCESS('获取到' + str(len(delete_user_ids)) + '条可删除用户'))

        UserCoin.objects.filter(user_id__in=delete_user_ids).delete()
        Record.objects.filter(user_id__in=delete_user_ids).delete()

        self.stdout.write(self.style.SUCCESS('清除成功'))
