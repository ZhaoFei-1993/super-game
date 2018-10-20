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
        i = 0
        s = 0
        a = 0
        for i in record_list:
            info = PromotionRecord()
            info.user = i.user
            if i.user.is_robot != 1:
                s += 1
                club_info = Club.objects.get_one(pk=i.roomquiz_id)
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
            else:
                a += 1
        print("足球，篮球转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")
        pk_list = RecordStockPk.objects.filter(created_at__gte=start_time)
        i = 0
        s = 0
        a = 0
        for i in pk_list:
            s += 1
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
        else:
            a += 1
        print("股票PK转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")

        guess_list = StockRecord.objects.filter(created_at__gte=start_time)
        i = 0
        s = 0
        a = 0
        for i in guess_list:
            info = PromotionRecord()
            info.user = i.user
            if i.user.is_robot != 1:
                s += 1
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
            else:
                a += 1
            print("股票转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")

        six_list = SixRecord.objects.filter(created_at__gte=start_time)
        i = 0
        s = 0
        a = 0
        for i in six_list:
            s += 1
            info = PromotionRecord()
            info.user = i.user
            if i.user.is_robot != 1:
                s += 1
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
            else:
                a += 1
            print("六合彩转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")

        dragontiger_list = Dragontigerrecord.objects.filter(created_at__gte=start_time)
        i = 0
        s = 0
        a = 0
        for i in dragontiger_list:
            info = PromotionRecord()
            info.user = i.user
            if i.user.is_robot != 1:
                s += 1
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
            else:
                a += 1
            print("龙虎斗转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")

        baccarat_list = Baccaratrecord.objects.filter(created_at__gte=start_time)
        i = 0
        s = 0
        a = 0
        for i in baccarat_list:
            info = PromotionRecord()
            info.user = i.user
            if i.user.is_robot != 1:
                s += 1
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
            else:
                a += 1
            print("百家乐转移记录完成！忽略机器人记录", a, "条， 存入真实用户记录", s, "条，一共", i, "条")





