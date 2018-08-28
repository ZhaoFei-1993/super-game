# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, DividendConfig, DividendConfigCoin, DividendHistory
from django.db import transaction
from datetime import datetime, timedelta
from django.db.models import Sum
from utils.functions import normalize_fraction


class Command(BaseCommand):
    """
    分红历史记录
    """
    help = "分红历史记录"


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('-----脚本开始运行-----'))
        now_date = datetime.now().date()
        last_date = now_date - timedelta(1)
        historys = DividendHistory.objects.all().order_by('-created_at')
        locks = UserCoinLock.objects.filter(is_free=0)
        is_history_exists = historys.exists()
        if is_history_exists:
            last_history = historys.first()
            last_dt = datetime.strptime(last_history.date, '%Y-%m-%d').date()
            if last_date==last_dt:
                raise CommandError("昨日分红已存在")
            else:
                if last_date-timedelta(1) == last_dt:
                    self.history_save(last_date, locks, is_history_exists=True)
                else:
                    delta = (now_date-last_dt).days
                    if delta < 0:
                        raise CommandError('分红日期错乱')
                    else:
                        for x in range(1, delta):
                            temp_date = last_dt + timedelta(x)
                            self.history_save(temp_date, locks, is_history_exists=True)
        else:
            self.history_save(last_date, locks)

        self.stdout.write(self.style.SUCCESS('-----脚本运行结束-----'))

    @staticmethod
    def null2zero(value):
        if value:
            return normalize_fraction(value,18)
        else:
            return 0


    def history_save(self, temp_date, locks, is_history_exists=False):
        history = DividendHistory()
        history.date = temp_date.strftime('%Y-%m-%d')
        history.deadline = self.null2zero(
            locks.filter(end_time__date=temp_date).aggregate(locks_sum=Sum('amount'))['locks_sum'])
        history.newline = self.null2zero(
            locks.filter(created_at__date=temp_date).aggregate(locks_sum=Sum('amount'))['locks_sum'])
        if not is_history_exists:
            history.locked = self.null2zero(
                locks.filter(created_at__date__lte=temp_date).aggregate(locks_sum=Sum('amount'))['locks_sum'])
        else:
            last_history = DividendHistory.objects.all().order_by('-created_at').first()
            history.locked = last_history.locked + history.newline
        history.truevalue = self.null2zero(
            DividendConfig.objects.filter(dividend_date__date=(temp_date + timedelta(1))).aggregate(
                locks_sum=Sum('dividend'))['locks_sum'])
        history.revenuevalue = self.null2zero(
            DividendConfigCoin.objects.filter(created_at__date=(temp_date + timedelta(1))).aggregate(
                locks_sum=Sum('revenue'))['locks_sum'])
        history.save()
        self.stdout.write(self.style.SUCCESS('-----新建日期为%s的记录-----' % history.date))
