# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import DailySettings, Coin



class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
      a=DailySettings.objects.all()
      coin=Coin.objects.get(id=4)
      for s in a:
          s.coin=coin
          s.save()