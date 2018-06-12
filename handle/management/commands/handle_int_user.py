# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from users.models import UserInvitation


class Command(BaseCommand):
    help = "handle int user"

    def handle(self, *args, **options):
        i = 1
        for user in UserInvitation.objects.filter(~Q(money=0), inviter_id=2638):
            print("i==============================", i)
            i += 1
            user.delete()
