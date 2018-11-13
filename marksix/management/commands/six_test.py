# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from marksix.models import MarkSixBetLimit, Option


class Command(BaseCommand, BaseView):
    help = "test"

    def handle(self, *args, **options):
        list = Option.objects.all()
        for i in list:
            betlimit = MarkSixBetLimit()
            betlimit.club_id = 10
            betlimit.options = i
            betlimit.max_limit = 5000
            betlimit.min_limit = 10
            betlimit.save()
