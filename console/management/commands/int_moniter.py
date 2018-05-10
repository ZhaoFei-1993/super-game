# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import requests
import json
import time
from base.eth import *
from users.models import UserCoin, UserRecharge, Coin


def get_txs():
    txs = dict()
    eth_wallet = Wallet()
    json_data = eth_wallet.get(url='v1/account/int/transaction/' + '0xA8C12Ef6a3Fc69Fe4E0Eb9966Adf8cb31cf04033')
    print(json_data.text)


class Command(BaseCommand):
    help = "INT监视器"

    def handle(self, *args, **options):
        get_txs()
