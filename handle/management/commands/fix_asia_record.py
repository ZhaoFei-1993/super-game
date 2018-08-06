# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from quiz.models import Quiz, Record, Rule


class Command(BaseCommand):

    def handle(self, *args, **options):
        list = []
        for quiz in Quiz.objects.all():
            if Rule.objects.filter(quiz=quiz, type='8').count() >= 2:
                list.append(quiz.id)
        print(list)


