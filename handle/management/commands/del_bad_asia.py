# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import *


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        bad_rules_list = []

        for quiz in Quiz.objects.filter(status=0):
            rules = Rule.objects.filter(quiz=quiz, tips='亚盘')
            if len(rules) > 1:
                bad_rules_list.append(rules.first().id)

        bad_option_list = list(Option.objects.filter(rule_id__in=bad_rules_list))

        QuizOddsLog.objects.filter(option_id__in=bad_option_list).delete()
        OptionOdds.objects.filter(option_id__in=bad_option_list).delete()
        Option.objects.filter(rule__in=bad_rules_list).delete()
        Rule.objects.filter(id__in=bad_rules_list).delete()
        print('删除成功')
