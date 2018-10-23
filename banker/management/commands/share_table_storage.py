# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from chat.models import Club
from banker.models import BankerShare


class Command(BaseCommand, BaseView):
    help = "份额表入库"

    def handle(self, *args, **options):
        club_list = Club.objects.all()
        for i in club_list:
            for s in range(1, 8):
                banker_share = BankerShare()
                banker_share.club = i
                banker_share.source = s
                if int(i.id) == 1:
                    b = 6000000000
                elif int(i.id) == 2:
                    b = 2000000
                elif int(i.id) == 3:
                    b = 280
                elif int(i.id) == 4:
                    b = 9
                elif int(i.id) == 5:
                    b = 10000
                elif int(i.id) == 6:
                    b = 60000
                elif int(i.id) == 7:
                    b = 120
                elif int(i.id) == 8:
                    b = 4000000
                else:
                    b = 40000000
                banker_share.balance = b
                banker_share.proportion = 0.4
                banker_share.save()
