# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from quiz.models import Category, Quiz


class Command(BaseCommand):
    """
    批量修改http为https
    """
    help = "批量修改http为https"

    def handle(self, *args, **options):
        quizs = Quiz.objects.all()
        for quiz in quizs:
            host_avatar = quiz.host_team_avatar.replace('http:', 'https:')
            guest_avatar = quiz.guest_team_avatar.replace('http:', 'https:')
            quiz.host_team_avatar = host_avatar
            quiz.guest_team_avatar = guest_avatar
            quiz.save()
            self.stdout.write(self.style.SUCCESS('地址成功 ' + quiz.host_team + ' VS ' + quiz.guest_team))
        # category = Category.objects.all()
        # for cate in category:
        #     if 'https:' in cate.icon or cate.icon == '':
        #         self.stdout.write(self.style.SUCCESS('ICON修改地址跳过 ' + cate.name))
        #         continue
        #     icon = cate.icon.replace('http:', 'https:')
        #     cate.icon = icon
        #     cate.save()
        #     self.stdout.write(self.style.SUCCESS('ICON修改地址成功 ' + cate.name))
