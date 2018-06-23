# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import DailySettings, Coin



class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
      a=DailySettings.objects.get(id=8)
      a.rewards = 200
      a.save()
      b=DailySettings.objects.get(id=9)
      b.rewards = 300
      b.save()
      c=DailySettings.objects.get(id=10)
      c.rewards = 400
      c.save()
      d=DailySettings.objects.get(id=11)
      d.rewards = 900
      d.save()
      e=DailySettings.objects.get(id=12)
      e.rewards = 1000
      e.save()
      f=DailySettings.objects.get(id=13)
      f.rewards = 1100
      f.save()
      i=DailySettings.objects.get(id=14)
      i.rewards = 2000
      i.save()
