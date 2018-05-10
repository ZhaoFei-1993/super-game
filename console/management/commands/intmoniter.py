# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import json
import time
from users.models import UserCoin, UserRecharge, Coin

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
}


class Command(BaseCommand):
    help = "INT监视器"

    def handle(self, *args, **options):
        print('1')
