# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import datetime
from django.db.models import Q
from quiz.models import Record, ClubProfitAbroad, Quiz, CashBackLog
from chat.models import Club
from users.models import CoinPrice, User
from utils.functions import normalize_fraction


class Command(BaseCommand):
    help = "计算现在用户拥有的gsg"

    def handle(self, *args, **options):
        gsg_sum = 0
        for user in User.objects.filter(is_block=False):
            gsg_sum = float(gsg_sum) + float(user.integral)
        print('现有gsg总量 =', gsg_sum)
