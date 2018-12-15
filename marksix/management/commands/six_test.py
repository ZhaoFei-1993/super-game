# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from marksix.models import SixRecord
from decimal import Decimal


class Command(BaseCommand, BaseView):
    help = "test"

    def handle(self, *args, **options):
        record_list = PromotionRecord.objects.filter(source=3)
        for i in record_list:
            record_id = int(i.record_id)
            info = SixRecord.objects.get(id=record_id)
            i.bets = Decimal(info.bet)*info.bet_coin
            i.save()
