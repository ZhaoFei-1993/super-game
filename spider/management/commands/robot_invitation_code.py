# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User, UserInvitation
from utils.functions import random_invitation_code
from django.db.models import Q
from api.settings import BASE_DIR
import os


class Command(BaseCommand):
    help = "给机器人分配邀请码"

    def handle(self, *args, **options):
        robot_list = User.objects.filter(is_robot=True, invitation_code='')
        for robot in robot_list:
            robot.invitation_code = random_invitation_code()
            robot.save()

        for robot in User.objects.filter(is_robot=True):
            invitee_number = UserInvitation.objects.filter(~Q(invitee_one=0), inviter=robot.id, is_effective=1).count()
            if int(invitee_number) < 5:
                os.chdir(BASE_DIR + '/cache')
                with open('invitation_code.lst', 'a+') as f:
                    f.write(robot.invitation_code)
                    f.write('\n')
