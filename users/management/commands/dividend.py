# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from users.models import UserCoinLock, Dividend
from quiz.models import Record, Quiz
from guess.models import Record as Record_Guess
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
        self.stdout.write(self.style.SUCCESS('-----分红脚本开始运行-----'))
        total_gsg = 1000000000
        now_date = datetime.now().date()
        count_date = now_date - timedelta(1)
        total_date = count_date.strftime('%Y-%m-%d')
        coin_locks = UserCoinLock.objects.filter(is_free=0, is_divided=0, created_at__date__lt=count_date, end_time__gt=datetime.now())
        print(total_date)

        #总下注额
        sql = "select  club_id, sum(bet) from "
        sql += " ("
        sql += " select roomquiz_id as club_id,  sum(bet) as bet from quiz_record a "
        sql += " join("
        sql += " select  quiz_record.id from quiz_record "
        sql += " where source <> '1'"
        # sql += "-- and earn_coin > 0"
        sql += " and  date_format(open_prize_time ,  '%Y-%m-%d') ='" + total_date +"'"
        sql += " )  b  on b.id=a.id"
        sql += " join ("
        sql += " select quiz_id  from quiz_record c "
        sql += " join (select  id from quiz_quiz where status='5') d on c.quiz_id = d.id"
        sql += " group by quiz_id) e on e.quiz_id= a.quiz_id"
        sql += " join( select a.id from users_user a"
        sql += "         inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += "        where b.count <=3 "
        sql += "        and is_robot=0 and is_block=0"
        sql += "        union "
        sql += "         select a.user_id as id from users_userrecharge a "
        sql += "         join users_user b on a.user_id=b.id"
        sql += "         where b.is_robot=0) f on f.id = a.user_id"
        sql += " group by roomquiz_id"
        sql += " union "
        sql += " select   club_id, sum(bets) as bet  from guess_record a "
        sql += " join( select a.id from users_user a"
        sql += "         inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += "        where b.count <=3 "
        sql += "        and is_robot=0 and is_block=0"
        sql += "        union "
        sql += "         select a.user_id as id from users_userrecharge a "
        sql += "         join users_user b on a.user_id=b.id"
        sql += "         where b.is_robot=0) c on c.id = a.user_id"
        sql += " where status = '1'"
        sql += " and source <> '4'"
        # sql += "-- and earn_coin > 0"
        sql += " and date_format(update_at, '%Y-%m-%d') = '" + total_date +"'"
        sql += " group by club_id) v"
        sql += " group by club_id"
        dt_all = self.list2dict(list(get_sql(sql)))

        #总发放额
        sql = "select  club_id, sum(earn_coin) from "
        sql += " ("
        sql += " select roomquiz_id as club_id,  sum(earn_coin) as earn_coin from quiz_record a "
        sql += " join("
        sql += " select  quiz_record.id from quiz_record "
        sql += " where source <> '1'"
        sql += " and earn_coin > 0"
        sql += " and  date_format(open_prize_time ,  '%Y-%m-%d') ='" + total_date +"'"
        sql += " )  b  on b.id=a.id"
        sql += " join ("
        sql += " select quiz_id  from quiz_record c "
        sql += " join (select  id from quiz_quiz where status='5') d on c.quiz_id = d.id"
        sql += " group by quiz_id) e on e.quiz_id= a.quiz_id"
        sql += " join( select a.id from users_user a"
        sql += "         inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += "        where b.count <=3 "
        sql += "        and is_robot=0 and is_block=0"
        sql += "        union "
        sql += "         select a.user_id as id from users_userrecharge a "
        sql += "         join users_user b on a.user_id=b.id"
        sql += "         where b.is_robot=0) f on f.id = a.user_id"
        sql += " group by roomquiz_id"
        sql += " union "
        sql += " select   club_id, sum(earn_coin) as earn_coin  from guess_record a "
        sql += " join( select a.id from users_user a"
        sql += "         inner join (select ip_address, count(username) as count from users_user group by ip_address) b on a.ip_address=b.ip_address"
        sql += "        where b.count <=3 "
        sql += "        and is_robot=0 and is_block=0"
        sql += "        union "
        sql += "         select a.user_id as id from users_userrecharge a "
        sql += "         join users_user b on a.user_id=b.id"
        sql += "         where b.is_robot=0) c on c.id = a.user_id"
        sql += " where status = '1'"
        sql += " and source <> '4'"
        sql += " and earn_coin > 0"
        sql += " and date_format(update_at, '%Y-%m-%d') = '" + total_date +"'"
        sql += " group by club_id) v"
        sql += " group by club_id"
        dt_earn = self.list2dict(list(get_sql(sql)))
        if dt_all:
            temp_dict={}
            for x in dt_all:
                if x not in dt_earn:
                    temp_dict[x] = dt_all[x]
                else:
                    temp_dict[x] = normalize_fraction(dt_all[x]-dt_earn[x],18)

            clubs = Club.objects.all()
            coins = []
            for x in clubs:
                for y in temp_dict.keys():
                    if x.id == int(y):
                        if x.coin.is_criterion!=1:
                            coins.append(
                                {
                                    'coin_id':x.coin_id,
                                    'profit':temp_dict[y]
                                }
                        )
            print('各种主要币种(除垃圾币)营收情况：', coins)
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
                self.stdout.write(self.style.SUCCESS('当前无锁定记录'))
        else:
            self.stdout.write(self.style.SUCCESS('昨日无开奖无分红'))
        self.stdout.write(self.style.SUCCESS('-----分红脚本结束运行-----'))

    def list2dict(self, result):
        temp={}
        if result:
            for x in result:
                temp[str(x[0])]=x[1]
        return temp