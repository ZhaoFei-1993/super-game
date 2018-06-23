# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import DailySettings, Coin



class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
      a=DailySettings.objects.get(id=8)
      a.rewards = 200
      s.save()
      a=DailySettings.objects.get(id=9)
      a.rewards = 300
      s.save()
      a=DailySettings.objects.get(id=10)
      a.rewards = 400
      s.save()
      a=DailySettings.objects.get(id=11)
      a.rewards = 900
      s.save()
      a=DailySettings.objects.get(id=12)
      a.rewards = 1000
      s.save()
      a=DailySettings.objects.get(id=13)
      a.rewards = 1100
      s.save()
      a=DailySettings.objects.get(id=14)
      a.rewards = 2000
      s.save()
