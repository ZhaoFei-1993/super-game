# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, LoginRecord
from utils.functions import random_invitation_code
from django.db.models import Q
from api.settings import BASE_DIR
import datetime


class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
        c = 1
        i = 1
        s = 1
        a = User.objects.filter(is_block=1).count()
        for user in User.objects.filter(is_block=1):
            if LoginRecord.objects.filter(user=user).exists() is not True:
                s += 1
            else:
                create_at = user.created_at
                log_st = LoginRecord.objects.filter(user=user).count()
                log_at = LoginRecord.objects.filter(user=user).order_by('login_time').first().login_time
                if log_at - create_at > datetime.timedelta(minutes=20):
                    i += 1
                if log_st > 5:
                    c += 1
        print("a==================================", a)
        print("c==================================", c)
        print("s==================================", s)
        print("i==================================", i)
