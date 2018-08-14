# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import shutil, os
from quiz.models import Quiz
from api.settings import BASE_DIR, MEDIA_DOMAIN_HOST


class Command(BaseCommand):
    help = "发送消息"

    def handle(self, *args, **options):
        img_dir = BASE_DIR + '/uploads/images/spider/football/team_icon'
        os.chdir(img_dir)
        for quiz in Quiz.objects.filter(category__parent_id=2):
            host_name = quiz.host_team
            guest_name = quiz.guest_team
            host_avatar = quiz.host_team_avatar.replace('https://api.gsg.one/images/spider/football/team_icon/', '')
            guest_avatar = quiz.guest_team_avatar.replace('https://api.gsg.one//images/spider/football/team_icon/', '')
            host_avatar_type = host_avatar.split('.')[1]
            guest_avatar_type = guest_avatar.split('.')[1]

            print(host_avatar, '===', host_name + '.' + host_avatar_type)
            print(guest_avatar, '===', guest_name + '.' + guest_avatar_type)

            # shutil.copy(host_avatar, host_name + '.' + host_avatar_type)
            # shutil.copy(guest_avatar, guest_name + '.' + guest_avatar_type)
