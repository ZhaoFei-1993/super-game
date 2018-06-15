# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserInvitation, User
from django.db.models import Q


class Command(BaseCommand):
    help = "删除世界杯记录"

    def handle(self, *args, **options):
        for i in User.objects.filter(is_robot=0, is_block=0):
            record_list = UserInvitation.objects.filter(money__gt=0, inviter_id=i.id, coin=9).count()
            if record_list > 5:
                print("=================================================", i.id)
                print("=================================================", record_list)
