# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from django.db.models import Q
from quiz.models import Record
from guess.models import Record as GuessRecord, RecordStockPk
from marksix.models import SixRecord


class Command(BaseCommand, BaseView):
    help = "联合做庄结算方法测试"

    def handle(self, *args, **options):
        promotion_record = PromotionRecord.objects.filter(~Q(status=0))
        for i in promotion_record:
            source = i.source
            record_id = i.record_id
            if source in (1, 2):
                list = Record.objects.get(id=record_id)
            elif source == 3:
                list = SixRecord.objects.get(id=record_id)
            elif source == 4:
                list = GuessRecord.objects.get(id=record_id)
            else:
                list = RecordStockPk.objects.get(id=record_id)
            i.open_prize_time = list.open_prize_time
            i.save()
