# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record
from django.db.models import Q


class Command(BaseCommand):
    help = "修改记录"

    def handle(self, *args, **options):
        record_list = Record.objects.filter(~Q(source=1))
        for record in record_list:
            if record.earn_coin == record.bet:
                record.type = 3
            if record.earn_coin == record.bet * record.odds:
                record.type = 1
            if str(record.earn_coin) == 0:
                record.type = 2
            record.save()
