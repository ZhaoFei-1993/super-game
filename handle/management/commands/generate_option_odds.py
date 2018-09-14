# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz, OptionOdds
from django.db.models import Q


class Command(BaseCommand):

    def handle(self, *args, **options):
        quiz_s = Quiz.objects.filter(Q(status='0') | Q(status='1'))
        for option_odds in OptionOdds.objects.filter(quiz__in=quiz_s, club_id=1):
            for new_club_id in [7, 8, 9]:
                new_option_odds = OptionOdds()
                new_option_odds.club_id = new_club_id
                new_option_odds.quiz = option_odds.quiz
                new_option_odds.option = option_odds.option
                new_option_odds.odds = option_odds.odds
                new_option_odds.save()

