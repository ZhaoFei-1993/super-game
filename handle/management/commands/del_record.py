# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record
from django.db.models import Q


class Command(BaseCommand):
    help = "删除世界杯记录"

    def handle(self, *args, **options):
        record_list = Record.objects.filter(Q(quiz_id__gte=313) | Q(quiz_id__lte=344), source=1)
        for record in record_list:
            record.delete()
