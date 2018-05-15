# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Category, Quiz
from users.models import IntegralPrize, User


class Command(BaseCommand):
    help = "Test"

    def handle(self, *args, **options):
        integralprizes = IntegralPrize.objects.all()
        i = 1
        for integralprize in integralprizes:
            dt = integralprize.icon.split(':')
            if dt[0] == 'https':
                continue
            else:
                integralprize.icon = dt[0] + 's:' + dt[1]
                i += 1
                print("i============================", i)
                integralprize.save()
    #     categorys = Category.objects.all()
    #     for category in categorys:
    #         if len(category.icon) > 0:
    #             dt = category.icon.split(':')
    #             if dt[0] == 'https':
    #                 continue
    #             else:
    #                 category.icon = dt[0] + 's:' + dt[1]
    #                 category.save()

    # quizs = Quiz.objects.all()
    # for quiz in quizs:
    #     dt_host = quiz.host_team_avatar.split(':')
    #     if dt_host[0] == 'https':
    #         continue
    #     else:
    #         quiz.host_team_avatar = dt_host[0] + 's:' + dt_host[1]
    #
    #     dt_guest = quiz.guest_team_avatar.split(':')
    #     if dt_guest[0] == 'https':
    #         continue
    #     else:
    #         quiz.guest_team_avatar = dt_guest[0] + 's:' + dt_guest[1]
    #
    #     quiz.save()

    # users = User.objects.all()
    # for user in users:
    #     dt = user.avatar.split(':')
    #     if dt[0] == 'https':
    #         continue
    #     else:
    #         user.avatar = dt[0] + 's:' + dt[1]
    #         user.save()
