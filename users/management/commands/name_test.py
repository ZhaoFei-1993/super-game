# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from users.models import UserMessage, CoinDetail


class Command(BaseCommand, BaseView):
    help = "删除"

    def handle(self, *args, **options):
        print("信息表删除开始")
        UserMessage.objects.filter(user__is_robot=1).delete()
        print("信息表删除完成")
        print("资金记录表删除开始")
        CoinDetail.objects.filter(user__is_robot=1).delete()
        print("资金记录表删除完成")
