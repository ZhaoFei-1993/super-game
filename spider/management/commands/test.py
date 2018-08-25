# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        quiz = Quiz.objects.get(match_flag='110123')
        quiz.host_team_fullname = '马来U23(中)'
        quiz.guest_team_fullname = '日本U23'
        quiz.save()
