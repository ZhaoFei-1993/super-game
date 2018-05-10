# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import json
import time
from users.models import UserCoin, UserRecharge, Coin


class Command(BaseCommand):
    help = "HAND监视器"

    def handle(self, *args, **options):
        print('1')
