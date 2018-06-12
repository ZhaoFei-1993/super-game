# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, LoginRecord


class Command(BaseCommand):
    help = "处理马甲"

    def handle(self, *args, **options):
        print('11111111111')
