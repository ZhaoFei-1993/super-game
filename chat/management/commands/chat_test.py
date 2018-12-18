# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from base.app import BaseView
from chat.models import ClubIncome, Club, ClubRule
from utils.functions import get_sql
from promotion.models import PromotionRecord
from users.models import CoinDetail
from decimal import Decimal
from django.conf import settings


class Command(BaseCommand, BaseView):
    help = "联合做庄结算方法测试"

    def handle(self, *args, **options):
        user_list = str(settings.TEST_USER_IDS)
        club_list = Club.objects.get_all()
        for i in club_list:
            club_info = i
            club_id = i.id
            if club_id == 1:
                continue
            club_rule = ClubRule.objects.all()
            info = {}
            for s in club_rule:
                type = int(s.id)
                if int(type) == 7:
                    type = 2
                elif int(type) == 1:
                    type = 1
                elif int(type) == 3:
                    type = 4
                elif int(type) == 2:
                    type = 3
                elif int(type) == 4:
                    type = 7
                    continue
                elif int(type) == 5:
                    type = 6
                    continue
                elif int(type) == 6:
                    type = 5
                sql_list = "date_format( p.created_at, '%Y-%m-%d' ) as years, "
                if type == 1:  # 足球
                    sql_list += "r.quiz_id as key_id, "
                elif type == 2:  # 篮球
                    sql_list += "r.quiz_id as key_id, "
                elif type == 3:  # 六合彩
                    sql_list += "r.issue as key_id, "
                elif type == 4:  # 股票
                    sql_list += "r.periods_id as key_id, "
                elif type == 5:  # 股票PK
                    sql_list += "r.issue_id as key_id, "
                sql_list += "sum(IF(p.earn_coin > 0, 0 - (p.earn_coin - p.bets), ABS(p.earn_coin))) as profit, "
                sql_list += "p.source"
                sql = "select " + sql_list + " from promotion_promotionrecord p"
                if type == 1:  # 足球
                    sql += " inner join quiz_record r on p.record_id=r.id"
                elif type == 2:  # 篮球
                    sql += " inner join quiz_record r on p.record_id=r.id"
                elif type == 3:  # 六合彩
                    sql += " inner join marksix_sixrecord r on p.record_id=r.id"
                elif type == 4:  # 股票
                    sql += " inner join guess_record r on p.record_id=r.id"
                elif type == 5:  # 股票PK
                    sql += " inner join guess_recordstockpk r on p.record_id=r.id"
                sql += " where p.club_id = '" + str(club_id) + "'"
                sql += " and p.source = '" + str(type) + "'"
                sql += " and p.user_id not in " + user_list
                sql += " group by years, key_id"
                # sql += " order by years desc"
                print("sql==========", sql)
                list_info = get_sql(sql)
                print("list_info================", list_info)
                for a in list_info:
                    print("1111111111111111")
                    key_name = ""
                    if a[3] == 1:
                        key_name = "足球"
                    elif a[3] == 2:
                        key_name = "篮球"
                    elif a[3] == 3:
                        key_name = "六合彩"
                    elif a[3] == 4:
                        key_name = "股票"
                    elif a[3] == 5:
                        key_name = "股票PK"
                    if key_name not in info:
                        info[key_name] = {}
                        if a[0] not in info[key_name]:
                            number = a[2]
                            if number > 0:
                                number = number*Decimal(str(0.95))
                            info[key_name][a[0]] = number
                        else:
                            number = a[2]
                            if number > 0:
                                number = number * Decimal(str(0.95))
                            info[key_name][a[0]] += number
                    else:
                        if a[0] not in info[key_name]:
                            number = a[2]
                            if number > 0:
                                number = number * Decimal(str(0.95))
                            info[key_name][a[0]] = number
                        else:
                            number = a[2]
                            if number > 0:
                                number = number * Decimal(str(0.95))
                            info[key_name][a[0]] += number
            print("info =================", info)
            for k in info:
                rule_name = 0
                if k == "足球":
                    rule_name = 1
                elif k == "篮球":
                    rule_name = 2
                elif k == "六合彩":
                    rule_name = 3
                elif k == "股票":
                    rule_name = 4
                elif k == "股票PK":
                    rule_name = 5
                print("rule_name==============", rule_name)
                for o in info[k]:
                    time = o + " 00:00:00"
                    print("time===============", time)
                    earn_coin = info[k][o]
                    print("coin_number==================", earn_coin)
                    club_income = ClubIncome()
                    club_income.club = club_info
                    club_income.earn_coin = earn_coin
                    club_income.created_at = time
                    club_income.source = rule_name
                    club_income.save()
