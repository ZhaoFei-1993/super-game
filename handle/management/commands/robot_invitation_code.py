# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, LoginRecord
from utils.functions import random_invitation_code
from django.db.models import Q
from api.settings import BASE_DIR
import os


class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
        i = 1
        for user in User.objects.filter(is_block=1):
            user_loging = LoginRecord.objects.filter(user_id=user.id).count()
            if user_loging < 0:
                i += 1
        print("i==================================", i)
