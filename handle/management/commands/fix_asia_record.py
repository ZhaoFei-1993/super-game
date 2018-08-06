# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Record


class Command(BaseCommand):
    help = "fix asia record"

    def handle(self, *args, **options):
        print('count =========== ', Record.objects.filter(rule__type='8', handicap='').count())
        for record in Record.objects.filter(rule__type='8', handicap=''):
            record.handicap = record.rule.handicap
            record.save()
