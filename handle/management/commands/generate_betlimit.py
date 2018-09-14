# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from marksix.models import MarkSixBetLimit
from chat.models import Club


class Command(BaseCommand):

    def handle(self, *args, **options):
        add_club_list = ['BCH俱乐部', 'SOC俱乐部', 'DB俱乐部']
        for bet_limit in MarkSixBetLimit.objects.filter(club_id=1):
            for club in Club.objects.filter(room_title__in=add_club_list):
                new_bet_limit = MarkSixBetLimit()
                new_bet_limit.options = bet_limit.options
                new_bet_limit.club = club
                if club.room_title == 'BCH俱乐部':
                    new_bet_limit.min_limit = 0.01
                    new_bet_limit.max_limit = 5
                elif club.room_title == 'SOC俱乐部':
                    new_bet_limit.min_limit = 50
                    new_bet_limit.max_limit = 100000
                elif club.room_title == 'DB俱乐部':
                    new_bet_limit.min_limit = 500
                    new_bet_limit.max_limit = 1000000
                new_bet_limit.save()


