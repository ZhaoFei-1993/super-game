# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        quiz = Quiz.objects.filter(id=10000000).first()
        print(quiz)
