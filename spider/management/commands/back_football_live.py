# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

class Command(BaseCommand):
    help = "爬取足球直播"

    def handle(self, *args, **options):
        print('lalala')
