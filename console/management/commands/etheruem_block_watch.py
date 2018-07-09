# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import requests
import json
import math
import sys
import logging
import time
from django.db import transaction
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler,FileSystemEventHandler
from decimal import Decimal
from users.models import UserCoin, UserRecharge, Coin, CoinDetail

monitor_path = '/var/log/supervisor'


class BlockMonitorHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == monitor_path + '/geth.log':
            with open(event.src_path) as f:
                data = f.readlines()
            last_line = data[-1]
            print('log file changed! %s' % last_line)


class Command(BaseCommand):
    help = "以太坊节点监视器"

    @transaction.atomic()
    def handle(self, *args, **options):
        event_handler = BlockMonitorHandler()
        observer = Observer()
        observer.schedule(event_handler, path=monitor_path, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()
