# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Club, OptionOdds


class Command(BaseCommand):
    help = "添加选项"

    def handle(self, *args, **options):
        usdt_club = Club.objects.get(room_title='USDT俱乐部')
        hand_club = Club.objects.get(room_title='HAND俱乐部')
        int = 1
        for optionodds in OptionOdds.objects.filter(club_id=hand_club.id):
            print("复制成功==================", int)
            int += 1
            new_optionodds = OptionOdds()
            new_optionodds.club = usdt_club
            new_optionodds.quiz = optionodds.quiz
            new_optionodds.option = optionodds.option
            new_optionodds.odds = optionodds.odds
            new_optionodds.save()
