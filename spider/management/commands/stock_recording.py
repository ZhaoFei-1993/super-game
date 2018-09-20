# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import RecordStockPk, Issues, OptionStockPk
from .stock_result_new import GuessPKRecording
import datetime


class Command(BaseCommand):
    help = "处理投注表"

    def handle(self, *args, **options):
        record_stock_pk = GuessPKRecording()
        option_obj_dic = {}
        for option in OptionStockPk.objects.all():
            option_obj_dic.update({
                option.id: {
                    'title': option.title,
                }
            })
        i = 0
        for issues in Issues.objects.filter(result_confirm__gte=3, is_open=False).order_by('id')[:10]:
            i += 1
            print('正在处理第 ', i, ' 期,issues_id=', issues.id, '   ', datetime.datetime.now())
            for record_pk in RecordStockPk.objects.filter(issue_id=issues.id, status=str(RecordStockPk.AWAIT)):
                record_stock_pk.pk_size(record_pk, option_obj_dic, issues)
                record_stock_pk.insert_info()
            issues.is_open = True
            issues.save()
        if i == 0:
            print('当前无需要处理的数据')
