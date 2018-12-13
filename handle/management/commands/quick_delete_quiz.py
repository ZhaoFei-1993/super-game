# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz, Rule, Option, OptionOdds, QuizOddsLog, Record


class Command(BaseCommand):

    def handle(self, *args, **options):
        quiz_id = 4576

        quiz = Quiz.objects.get(id=quiz_id)
        if Record.objects.filter(quiz=quiz, source=str(Record.NORMAL)).exists() is not True:
            print('无用户投注可以删除quiz')

            rules_list = Rule.objects.filter(quiz_id=quiz.id)
            QuizOddsLog.objects.filter(quiz_id=quiz.id).delete()
            OptionOdds.objects.filter(quiz_id=quiz.id).delete()
            Option.objects.filter(rule__in=rules_list).delete()
            rules_list.delete()
            quiz.delete()

            print('删除成功')
        else:
            print('不可以删除要先处理真实用户投注')
