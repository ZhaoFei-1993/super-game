# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Rule, Option


class Command(BaseCommand):
    help = "更新选项"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        i = 0

        for rule in Rule.objects.filter(type=str(Rule.RESULTS)):
            rule.tips_en = ' Winner'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.POLITENESS_RESULTS), tips_en=''):
            rule.tips_en = 'Handicap Results'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.SCORE)):
            rule.tips_en = 'Scored'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.TOTAL_GOAL), tips_en=''):
            rule.tips_en = 'Total goals'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.RESULT)):
            rule.tips_en = ' Winner'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.POLITENESS_RESULT), tips_en=''):
            rule.tips_en = 'Handicap Results'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.SIZE_POINTS), tips_en=''):
            rule.tips = '大小分'
            rule.tips_en = 'Compare the total score'
            rule.save()
            i += 1
            print('========================> i = ', i)

        for rule in Rule.objects.filter(type=str(Rule.VICTORY_GAP), tips_en=''):
            rule.tips_en = 'Wins the gap'
            rule.save()
            i += 1
            print('========================> i = ', i)

        # for option in Option.objects.all():
        #     if '主胜' in option.option:
        #         option.option_en = 'Home'
        #     elif '主负' in option.option:
        #         option.option_en = 'Away'
        #     elif '平局' in option.option:
        #         option.option_en = 'Draw'
        #     elif ':' in option.option:
        #         option.option_en = option.option
        #     elif '球' in option.option:
        #         if option.option[0] == '7':
        #             option.option_en = '7+'
        #         else:
        #             option.option_en = option.option[0]
        #     elif option.option == '胜其他' or option.option == '平其他' or option.option == '负其他':
        #         option.option_en = 'Other'
        #     elif '-' in option.option:
        #         option.option_en = option.option
        #     elif '总分大于' in option.option:
        #         option.option_en = 'More than ' + option.option[4:]
        #     elif '总分小于' in option.option:
        #         option.option_en = 'Less than ' + option.option[4:]
        #
        #     option.save()

            # i += 1
            # print('========================> i = ', i)

        print('>>>>>>>>>>>>>>>>>>>>>>>> 结束 >>>>>>>>>>>>>>>>>>>>>>>>')
