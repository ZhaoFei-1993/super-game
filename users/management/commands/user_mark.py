# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from users.models import User, RecordMark
from utils.functions import get_sql


class Command(BaseCommand, BaseView):
    help = "用户生成标记表记录"

    def handle(self, *args, **options):
        user_list_number = User.objects.all().count()
        user_list_number = user_list_number*6
        user_list = User.objects.all()
        number = 0
        for i in user_list:
            for s in range(1, 7):
                record_mark = RecordMark()
                record_mark.user_id = i.id
                record_mark.rule = s
                record_mark.status = 0
                record_mark.save()
                number += 1
                print("一共=============", user_list_number, "条， 录入成功=======================", number, "条")

