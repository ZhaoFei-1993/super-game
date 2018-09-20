# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from guess.models import Issues, Periods
from spider.management.commands.stock_result_new import new_issues


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Connection': 'close',
}


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        left_periods = Periods.objects.get(id=173)
        right_periods = Periods.objects.get(id=172)
        new_issues(left_periods, right_periods, '09:30:00')






