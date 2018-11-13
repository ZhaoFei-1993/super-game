# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from guess.models import BetLimit, Play


class Command(BaseCommand, BaseView):
    help = "test"

    def handle(self, *args, **options):
        list = Play.objects.all()
        for i in list:
            betlimit = BetLimit()
            betlimit.club_id = 10
            betlimit.play_id = i.id
            betlimit.bets_one = 10
            betlimit.bets_two = 100
            betlimit.bets_three = 500
            betlimit.bets_min = 10
            betlimit.bets_max = 5000
            betlimit.save()
