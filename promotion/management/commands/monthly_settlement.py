# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
import random
from base.app import BaseView
import datetime
from datetime import timedelta
from utils.functions import get_sql, reward_gradient_all, opposite_number
from promotion.models import PresentationMonth
from users.models import UserCoin

class Command(BaseCommand, BaseView):
    help = "推广人月结算"

    def handle(self, *args, **options):
        # this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
        # end = this_month_start - timedelta(days=1)  # 上个月的最后一天
        # start_time = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
        # end_time = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'

        year = datetime.date.today().year  # 获取当前年份
        month = datetime.date.today().month  # 获取当前月份
        start = datetime.date(year, month, day=1).strftime('%Y-%m-%d')  # 获取当月第一天
        start_time = str(start) + ' 00:00:00'
        created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
        end_time = str(created_at_day) + ' 23:59:59'  # 一天结束时间

        sql_list = "sum(pu.bet_water), sum(pu.dividend_water), sum(pu.income), pu.user_id, pu.club_id, c.coin_id"
        sql = "select " + sql_list + " from promotion_userpresentation pu"
        sql += " inner join chat_club c on pu.club_id=c.id"
        sql += " where pu.created_at >= '" + str(start_time) + "'"
        sql += " and pu.created_at <= '" + str(end_time) + "'"
        sql += " and pu.club_id not in (1, 5)"
        sql += " group by pu.user_id, pu.club_id"
        userpresentation_list = get_sql(sql)
        for i in userpresentation_list:
            income = i[2]
            print("income=============================", income)
            proportion = reward_gradient_all(i[4], i[2])
            income_dividend = proportion*opposite_number(i[2])
            presentation_month = PresentationMonth()
            presentation_month.user_id = i[3]
            presentation_month.club_id = i[4]
            presentation_month.income = i[2]
            presentation_month.income_dividend = income_dividend
            presentation_month.proportion = proportion
            presentation_month.is_receive = 1
            presentation_month.created_at = start_time
            presentation_month.save()
            if income_dividend > 0:
                coin_info = UserCoin.objects.get(user_id=i[3], coin_id=i[5])
                coin_info.balance += income_dividend
                coin_info.save()
