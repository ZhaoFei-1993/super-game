# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST
import os
cache_dir = BASE_DIR + '/cache'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}

class Command(BaseCommand):
    help = "爬取足球足球联赛"

    def handle(self, *args, **options):
        os.chdir(cache_dir)
        files = []
        for root, sub_dirs, files in list(os.walk(cache_dir))[0:1]:
            files = files
        print(files)