# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from chat.models import Club
from banker.models import BankerShare


class Command(BaseCommand, BaseView):
    help = "份额表入库"

    def handle(self, *args, **options):
        club_list = BankerShare.objects.all()
        for i in club_list:
            if int(i.club_id) == 1:
                b = 5000000000
                s = 2000000000
            elif int(i.club_id) == 2:
                b = 21000000
                s = 8400000
            elif int(i.club_id) == 3:
                b = 4000
                s = 1600
            elif int(i.club_id) == 4:
                b = 100
                s = 40
            elif int(i.club_id) == 5:
                b = 150000
                s = 60000
            elif int(i.club_id) == 6:
                b = 450000
                s = 180000
            elif int(i.club_id) == 7:
                b = 2300
                s = 920
            elif int(i.club_id) == 8:
                b = 90000000
                s = 36000000
            else:
                b = 275000000
                s = 110000000
            i.balance = b
            i.all_balance = s
            i.save()
