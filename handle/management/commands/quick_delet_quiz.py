# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz, Rule, Option, OptionOdds, QuizOddsLog, Record


class Command(BaseCommand):

    def handle(self, *args, **options):
        quiz = Quiz.objects.get(id=4576)
        rules_list = Rule.objects.filter(quiz_id=quiz.id)
        QuizOddsLog.objects.filter(quiz_id=quiz.id).delete()
        OptionOdds.objects.filter(quiz_id=quiz.id).delete()
        Option.objects.filter(rule__in=rules_list).delete()
        rules_list.delete()
        quiz.delete()
