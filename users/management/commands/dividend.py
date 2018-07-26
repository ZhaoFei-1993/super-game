# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, Dividend
from quiz.models import Record, Quiz
from chat.models import Club
from django.db.models import Q, Sum
from utils.functions import normalize_fraction, get_sql
from django.db import transaction
from datetime import datetime, timedelta


class Command(BaseCommand):
    """
    每日分红
    """
    help = "每日分红"

    @transaction.atomic()
    def handle(self, *args, **options):
        total_gsg = 1000000000
        now_date = datetime.now().date()
        count_date = now_date - timedelta(1)
        coin_locks = UserCoinLock.objects.filter(is_free=0, is_divided=0, created_at__date__lt=count_date)
        sql = "select a.id from users_user a"
        sql += " inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += " where b.count <=3 "
        sql += " and is_robot=0 and is_block=0"
        dt_all = list(get_sql(sql))

        sql = "select distinct(user_id) from users_userrecharge"
        dt_recharge = list(get_sql(sql))

        dt_all = list(set(dt_all + dt_recharge))
        dd = []
        for x in dt_all:
            dd.append((x[0]))
        # users = '(' + ','.join(dd) + ')'

        # quizs= Quiz.objects.filter(status=Quiz.BONUS_DISTRIBUTION)

        bets = Record.objects.filter(~Q(source=Record.CONSOLE), quiz__status=Quiz.BONUS_DISTRIBUTION, open_prize_time__date=count_date, user_id__in=dd).values('roomquiz_id').annotate(Sum('bet')).order_by('roomquiz_id')
        sent_coin = Record.objects.filter(~Q(source=Record.CONSOLE), quiz__status=Quiz.BONUS_DISTRIBUTION, open_prize_time__date=count_date, user_id__in=dd, earn_coin__gt= 0).values('roomquiz_id').annotate(Sum('earn_coin')).order_by('roomquiz_id')
        temp_list=[]
        if bets.exists():
            if not sent_coin.exists():
                for a in bets:
                    temp_list.append({
                        'roomquiz_id': a['roomquiz_id'],
                        'profit': normalize_fraction(a['bet__sum'], 18)
                    })
            else:
                rooms = []
                earns = {}
                for b in sent_coin:
                    rooms.append(b['roomquiz_id'])
                    earns[str(b['roomquiz_id'])] = b['earn_coin__sum']
                for a in bets:
                    if a['roomquiz_id'] not in rooms:
                        temp_list.append({
                            'roomquiz_id': a['roomquiz_id'],
                            'profit': normalize_fraction(a['bet__sum'], 18)
                        })
                    else:
                        temp_list.append({
                            'roomquiz_id': a['roomquiz_id'],
                            'profit': normalize_fraction(a['bet__sum'] - earns[str(a['roomquiz_id'])], 18)})

            coins = []
            if temp_list:
                for x in temp_list:
                    try:
                        club = Club.objects.get(id=x['roomquiz_id'])
                    except Exception:
                        raise
                    if club.coin.is_criterion != 1:
                        coins.append(
                            {'coin_id':club.coin_id,
                             'profit':x['profit']
                         })
            if coin_locks.exists():
                for x in coin_locks:
                    for y in coins:
                        if y['profit'] > 0:
                            divide = Dividend()
                            divide.coin_id=y['coin_id']
                            divide.user_lock_id=x.id
                            divide.divide = normalize_fraction((x.amount/total_gsg)*y['profit'], 18)
                            divide.save()
                self.stdout.write(self.style.SUCCESS('分红完成'))
            else:
                raise CommandError('当前无锁定记录')
        else:
            self.stdout.write(self.style.SUCCESS('今日无开奖无分红'))
