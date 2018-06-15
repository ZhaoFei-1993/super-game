# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import IntInvitation, User


class Command(BaseCommand):
    help = "block invitation"

    def handle(self, *args, **options):
        i = 0
        for int_invitation in IntInvitation.objects.all():
            user = User.objects.get(pk=int_invitation.invitee)
            if user.is_block is True:
                int_invitation.is_block = True
                int_invitation.save()

                i += 1
                print('=====================> i= ', i)
