# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from .mark_six_result import ergodic_record
from spider.management.commands.mark_six import color_dic
from itertools import combinations
from guess.models import Record


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        for i in range(4000):
            print(i)
            record = Record()
            record.bets = 2
            record.odds = 1.95
            record.periods_id = 168
            record.user_id = 1427
            record.club_id = 6
            record.play_id = 9
            record.options_id = 3
            record.save()
