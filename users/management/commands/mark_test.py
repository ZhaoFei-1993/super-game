# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from marksix.models import SixRecord


class Command(BaseCommand, BaseView):
    help = "test"

    def handle(self, *args, **options):
        list = PromotionRecord.objects.filter(source=3)
        for i in list:
            six = SixRecord.objects.get(pk=i.record_id)
            i.bets = six.bet_coin
            i.save()
