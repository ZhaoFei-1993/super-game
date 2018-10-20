# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from quiz.models import Record
from guess.models import RecordStockPk, Record as StockRecord
from marksix.models import SixRecord
from dragon_tiger.models import Dragontigerrecord
from baccarat.models import Baccaratrecord
from chat.models import Club

class Command(BaseCommand, BaseView):
    help = "下注记录转移"

    def handle(self, *args, **options):
        start_time = '2018-10-18 01:00:00'  # 开始时间
        record_list = Record.objects.filter(created_at__gte=start_time)
        for i in record_list:
            info = PromotionRecord()
            info.user = i.user
            club_info = Club.objects.get_one(i.roomquiz_id)
            info.club = club_info
            info.bets = i.bet
            info.earn_coin = i.earn_coin
            if int(i.quiz.category.parent) == 1:
                source = 2
            else:
                source = 1
            info.source = source
            if int(i.type) == 1:
                status = 1
            elif int(i.type) == 2 or int(i.type) == 3:
                status = 2
            else:
                status = 3
            info.status = status
            info.created_at = i.created_at
            info.save()

        pk_list = RecordStockPk.objects.filter(created_at__gte=start_time)
        for i in pk_list:
            info = PromotionRecord()
            info.user = i.user
            info.club = i.club
            info.bets = i.bets
            info.earn_coin = i.earn_coin
            info.source = 5
            if int(i.status) == 0:
                status = 1
            elif int(i.status) == 1:
                status = 2
            else:
                status = 3
            info.status = status
            info.created_at = i.created_at
            info.save()

        guess_list = StockRecord.objects.filter(created_at__gte=start_time)
        for i in guess_list:
            info = PromotionRecord()
            info.user = i.user
            info.club = i.club
            info.bets = i.bets
            info.earn_coin = i.earn_coin
            info.source = 4
            if int(i.status) == 0:
                status = 1
            elif int(i.status) == 1:
                status = 2
            else:
                status = 3
            info.status = status
            info.created_at = i.created_at
            info.save()

        six_list = SixRecord.objects.filter(created_at__gte=start_time)
        for i in six_list:
            info = PromotionRecord()
            info.user = i.user
            info.club = i.club
            info.bets = i.bet_coin
            info.earn_coin = i.earn_coin
            info.source = 3
            if int(i.type) == 0:
                status = 1
            else:
                status = 2
            info.status = status
            info.created_at = i.created_at
            info.save()

        dragontiger_list = Dragontigerrecord.objects.filter(created_at__gte=start_time)
        for i in dragontiger_list:
            info = PromotionRecord()
            info.user = i.user
            info.club = i.club
            info.bets = i.bets
            info.earn_coin = i.earn_coin
            info.source = 7
            if int(i.type) == 0:
                status = 1
            elif int(i.type) == 1:
                status = 2
            else:
                status = 3
            info.status = status
            info.created_at = i.created_at
            info.save()

        baccarat_list = Baccaratrecord.objects.filter(created_at__gte=start_time)
        for i in baccarat_list:
            info = PromotionRecord()
            info.user = i.user
            info.club = i.club
            info.bets = i.bets
            info.earn_coin = i.earn_coin
            info.source = 6
            if int(i.type) == 0:
                status = 1
            elif int(i.type) == 1:
                status = 2
            else:
                status = 3
            info.status = status
            info.created_at = i.created_at
            info.save()





