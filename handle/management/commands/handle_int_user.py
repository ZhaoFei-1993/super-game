# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from users.models import UserInvitation


class Command(BaseCommand):
    help = "handle int user"

    def handle(self, *args, **options):
        for user in UserInvitation.objects.filter(~Q(is_money=0), inviter_id=2638):
            user.delete()
