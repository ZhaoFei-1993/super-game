# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from users.models import User
from base.app import BaseView


class Command(BaseCommand, BaseView):
    help = "处理相同注册ip用户"

    def handle(self, *args, **options):
        print('>>>>>>>>>>>>>>>>>>>>>>>> 开始 >>>>>>>>>>>>>>>>>>>>>>>>')
        sql = "SELECT SUBSTRING_INDEX(ip_address, '.', 3) as subip, count(*) as cnt "
        sql += "FROM users_user u WHERE ip_address != '' GROUP BY subip HAVING cnt >= 50 order by cnt desc"
        same_ips = self.get_all_by_sql(sql)

        for ip in same_ips:
            ip_prefix = ip[0]
            user_total = User.objects.filter(ip_address__startswith=ip_prefix, is_block=0).count()
            print('ip = ', ip_prefix, ' 共禁用 ', user_total, ' 个账号')
            # User.objects.filter(ip_address__startswith=ip_prefix, is_block=0).update(is_block=1)
