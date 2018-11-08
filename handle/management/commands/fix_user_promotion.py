# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from promotion.models import UserPresentation, PromotionRecord
import datetime


class Command(BaseCommand):
    help = "fix_user_promotions"

    def handle(self, *args, **options):
        print('Go Time')
        bagin_time = datetime.datetime.strptime('2018-09-07 00:00:00', '%Y-%m-%d %H:%M:%S')
        records = PromotionRecord.objects.filter(created_at__gt=bagin_time, status=1)
        print('共', len(records), '条')
        UserPresentation.objects.club_flow_statistics(records, 7)
        print('End Time')

