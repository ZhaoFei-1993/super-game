# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from base.app import BaseView
from utils.cache import get_cache


class Command(BaseCommand, BaseView):
    help = "tttt"

    def add_arguments(self, parser):
        parser.add_argument('key', type=str, help='Redis键值')

    def handle(self, *args, **options):
        key = options['key']
        print('value = ', get_cache(key))
