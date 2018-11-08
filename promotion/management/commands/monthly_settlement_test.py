# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from promotion.models import PromotionRecord
from quiz.models import Record
from guess.models import RecordStockPk, Record as GuessRecord
from marksix.models import SixRecord


class Command(BaseCommand, BaseView):
    help = "推广人月结算"

    def handle(self, *args, **options):
        list = PromotionRecord.objects.all()
        for i in list:
            print("source============================", i.source)
            print("record_id========================", i.record_id)
            s = [19942132, 19942133, 19942132]
            if int(i.record_id) == 19942133:
                i.delete()
            else:
                if int(i.source) == 1 or int(i.source) == 2:
                    record_list = Record.objects.get(pk=i.record_id)
                    if int(record_list.type) == 0:
                        status = 0
                    elif int(record_list.type) == 1 and int(record_list.type) == 2:
                        status = 1
                    else:
                        status = 2
                    i.status = status
                elif int(i.source) == 3:
                    record_list = SixRecord.objects.get(pk=i.record_id)
                    if int(record_list.status) == 0:
                        status = 0
                    else:
                        status = 1
                    i.status = status
                elif int(i.source) == 5:
                    record_list = RecordStockPk.objects.get(pk=i.record_id)
                    if int(record_list.status) == 0:
                        status = 0
                    elif int(record_list.status) == 1:
                        status = 1
                    else:
                        status = 2
                    i.status = status
                else:
                    record_list = GuessRecord.objects.get(pk=i.record_id)
                    if int(record_list.status) == 0:
                        status = 0
                    elif int(record_list.status) == 1:
                        status = 1
                    else:
                        status = 2
                    i.status = status
                i.save()
