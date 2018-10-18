# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from time import sleep
import random
from django.core.management import call_command


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        for i in range(200):
            call_command('stock_recording')

















