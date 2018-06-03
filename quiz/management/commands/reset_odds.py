# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from quiz.models import Quiz, OptionOdds, Option, Quiz_Odds_Log
from datetime import datetime


class Command(BaseCommand):
    help = "恢复初始赔率"

    def handle(self, *args, **options):
        # 获取正在进行的比赛
        quizs = Quiz.objects.filter(status=Quiz.PUBLISHING, is_delete=False, begin_at__gt=datetime.now())
        # quizs = Quiz.objects.filter(status=Quiz.PUBLISHING, is_delete=False)
        if len(quizs) == 0:
            raise CommandError('当前无进行中的竞猜')

        for quiz in quizs:
            # 获取竞猜初始赔率
            odds_log = Quiz_Odds_Log.objects.filter(quiz=quiz)
            for odd_log in odds_log:
                # 获取该玩法下的所有选项
                options = Option.objects.filter(rule_id=odd_log.rule_id)
                for option in options:
                    if option.option == odd_log.option:
                        OptionOdds.objects.filter(option_id=option.id).update(odds=odd_log.odds)

                        self.stdout.write(self.style.SUCCESS(option.option + '赔率调整为: ' + str(odd_log.odds)))


