# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from chat.models import Club


class Command(BaseCommand):
    help = "在线人数波动"

    def handle(self, *args, **options):
        result = Club.objects.fluctuation_club_online()
        if result is True:
            print("人数波动已经完成！")
