# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import UserMessage


class Command(BaseCommand):
    help = "删除消息"

    def handle(self, *args, **options):
        is_user = UserMessage.objects.filter(message_id=15)
        for user in is_user:
            user.status = 2
            user.save()