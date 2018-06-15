# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from users.models import UserInvitation, User


class Command(BaseCommand):
    help = "handle int user"

    def handle(self, *args, **options):
        i = 1
        for user in UserInvitation.objects.filter(~Q(invitee_one=0), inviter_id=15957):
            print("================================================", i, "===========================", user.invitee_one)
            i = i+1
            user_list = User.objects.get(id=user.invitee_one)
            user_list.is_block = 1
            user_list.save()
