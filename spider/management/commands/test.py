# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Category, Quiz
from users.models import IntegralPrize, User


class Command(BaseCommand):
    help = "Test"

    def handle(self, *args, **options):
        categorys = Category.objects.all()
        for category in categorys:
            if len(category.icon) > 0:
                dt = category.icon.split(':')
                category.icon = dt[0] + 's:' + dt[1]
                category.save()

        quizs = Quiz.objects.all()
        for quiz in quizs:
            dt_host = quiz.host_team_avatar.split(':')
            dt_guest = quiz.guest_team_avatar.split(':')
            quiz.host_team_avatar = dt_host[0] + 's:' + dt_host[1]
            quiz.guest_team_avatar = dt_guest[0] + 's:' + dt_guest[1]
            quiz.save()

        integralprizes = IntegralPrize.objects.all()
        for integralprize in integralprizes:
            dt = integralprize.icon.split(':')
            integralprize.icon = dt[0] + 's:' + dt[1]
            integralprize.save()

        users = User.objects.all()
        for user in users:
            dt = user.avatar.split(':')
            user.avatar = dt[0] + 's:' + dt[1]
            user.save()
