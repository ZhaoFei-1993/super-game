# -*- coding: utf-8 -*-

from django.db.models import Q
from django.core.management.base import BaseCommand
from quiz.models import ChangeRecord
from users.models import UserCoin

class Command(BaseCommand):
    help = "删除正式库机器人兑换的GSG"

    def handle(self, *args, **options):
        all_change = ChangeRecord.objects.all()
        i=1
        for change in all_change:
            user_id = change.user.id
            user_coin = UserCoin.objects.get(user_id=user_id, coin_id=6)
            if user_coin.balance < change.change_gsg_value:
                user_coin.balance = 0
            else:
                user_coin.balance -= change.change_gsg_value
            user_coin.save()
            print("--------------------已处理"+i+"个用户----------回收"+change.change_gsg_value+"个gsg--------------------------")
            i+=1