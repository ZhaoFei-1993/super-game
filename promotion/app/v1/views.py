# -*- coding: UTF-8 -*-
from base.app import CreateAPIView, ListCreateAPIView, ListAPIView, DestroyAPIView, RetrieveAPIView, \
    RetrieveUpdateAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
import os
from django.conf import settings
from utils.functions import random_invitation_code
import pygame
from PIL import Image
import qrcode
from chat.models import Club
from django.db.models import Q, Sum
from users.models import UserInvitation
import datetime
from users.models import Coin
from promotion.models import UserPresentation
import calendar
import re
from datetime import timedelta
from utils.functions import normalize_fraction, value_judge, get_sql, reward_gradient, opposite_number, reward_gradient_all
from decimal import Decimal
import time



class PromotionInfoView(ListAPIView):
    """
    用户邀请信息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        nowadays_day = datetime.datetime.now().strftime('%Y-%m-%d')
        nowadays_now = str(nowadays_day) + ' 00:00:00'
        print("nowadays_day===============", nowadays_day)
        print("nowadays_now===============", nowadays_now)
        nowadays_old = str(nowadays_day) + ' 23:59:59'
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_now = str(yesterday) + ' 00:00:00'
        yesterday_old = str(yesterday) + ' 23:59:59'
        print("yesterday_now======================", yesterday_now)
        print("yesterday_old========================", yesterday_old)

        user_avatar = user.avatar          # 用户头像
        nowadays_number = UserInvitation.objects.filter(Q(created_at__lte=nowadays_old),Q(created_at__gte=nowadays_now), inviter_id=user.id).count()            # 今天邀请人数
        yesterday_number = UserInvitation.objects.filter(Q(created_at__lte=yesterday_old),Q(created_at__gte=yesterday_now), inviter_id=user.id).count()        # 昨天邀请人数
        all_user_number = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1).count()        # 总邀请人数
        all_user_gsg = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1, status=2).aggregate(Sum('money'))
        sum_gsg = all_user_gsg['money__sum'] if all_user_gsg['money__sum'] is not None else 0                     # 总邀请获得GSG数
        qr_data = settings.SUPER_GAME_SUBDOMAIN + '/#/register?from_id=' + str(user.id)
        return self.response({'code': 0, "data": {
            "user_avatar": user_avatar,
            "nowadays_number": nowadays_number,
            "yesterday_number": yesterday_number,
            "all_user_number": all_user_number,
            "sum_gsg": sum_gsg,
            "qr_data": qr_data,
        }})


class PromotionListView(ListAPIView):
    """
    邀请俱乐部流水
    """

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        type = self.request.GET.get('type')
        regex = re.compile(r'^(1|2|3|4)$')              # 1.今天 2.昨天 3.本月 4.上月
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

        coin_id_list = []
        all_club = Club.objects.filter(~Q(pk=1))
        club_list = []
        coins = Coin.objects.get_all()
        map_coin = {}
        for coin in coins:
            map_coin[coin.id] = coin
        for i in all_club:
            coin_id_list.append(str(i.id))
            coin = map_coin[i.coin.id]
            club_list.append({
                "club_id": i.id,
                "club_icon": i.icon,
                "coin_name": coin.name,
                "coin_id": coin.id,
                "coin_accuracy": coin.coin_accuracy
            })


        year = datetime.date.today().year  # 获取当前年份
        month = datetime.date.today().month  # 获取当前月份
        weekDay, monthCountDay = calendar.monthrange(year, month)  # 获取当月第一天的星期和当月的总天数
        start = datetime.date(year, month, day=1).strftime('%Y-%m-%d')  # 获取当月第一天
        month_first_day = str(start) + ' 00:00:00'           # 这个月的开始时间

        if int(type) == 1:          # 今天
            created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
            start = str(created_at_day) + ' 00:00:00'  # 一天开始时间
            end = str(created_at_day) + ' 23:59:59'  # 一天结束时间
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(month_first_day) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
            print("monthly_summary======================", monthly_summary)
        elif int(type) == 2:             # 昨天
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            start = str(yesterday) + ' 00:00:00'
            end = str(yesterday) + ' 23:59:59'
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(month_first_day) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        elif int(type) == 3:        # 当月
            end = datetime.date(year, month, day=monthCountDay).strftime('%Y-%m-%d')           # 获取当前月份最后一天
            start = str(start) + ' 00:00:00'
            end = str(end) + ' 23:59:59'
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(start) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        else:              # 上月
            this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
            end = this_month_start - timedelta(days=1)              # 上个月的最后一天
            start = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'       # 上个月i第一天
            end = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(start) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        monthly_summarys = {}
        for s in monthly_summary:
            monthly_summarys[s[1]] = s[0]

        sql = "select club_id, sum(pu.bet_water) as sum_bet_water, sum(pu.dividend_water), sum(pu.income) from promotion_userpresentation pu"
        sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(start) + "'"
        sql += " and pu.created_at <= '" + str(end) + "'"
        sql += " group by pu.club_id"
        coin_number = get_sql(sql)
        coin_number_info = {}
        for s in coin_number:
            coin_number_info[int(s[0])] = s
        data = []
        for i in club_list:
            if i["club_id"] in coin_number_info:
                income_dividend = reward_gradient(user.id, i["club_id"], monthly_summarys[i["club_id"]])
                all_income_dividend = Decimal(coin_number_info[i["club_id"]][3])
                all_income_dividend = opposite_number(all_income_dividend)
                income_dividends = all_income_dividend * Decimal(income_dividend)

                i["bet_water"] = normalize_fraction(coin_number_info[i["club_id"]][1], i["coin_accuracy"])
                i["dividend_water"] = normalize_fraction(coin_number_info[i["club_id"]][2], i["coin_accuracy"])
                i["income"] = normalize_fraction(coin_number_info[i["club_id"]][3], i["coin_accuracy"])
                i["income_dividends"] = normalize_fraction(income_dividends, i["coin_accuracy"])
            else:
                i["bet_water"] = 0
                i["dividend_water"] = 0
                i["income"] = 0
                i["income_dividends"] = 0
            data.append(i)
        return self.response({'code': 0, 'data': data})



class PromotioncClubView(ListAPIView):
    """
    收入
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = self.request.GET.get('club_id')
        if int(club_id) == 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

        sql = "select u.coin_accuracy, u.icon from chat_club c"
        sql += " inner join users_coin u on c.coin_id=u.id"
        sql += " where c.id = '" + str(club_id) + "'"
        club_info = get_sql(sql)[0]
        coin_accuracy = club_info[0]
        coin_icon = club_info[1]

        sql = "select sum(pu.bet_water), sum(pu.dividend_water) from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        all_amount = get_sql(sql)[0]
        if all_amount[0] is None or all_amount[0] == 0:
            all_bet_water = 0
        else:
            all_bet_water = normalize_fraction(all_amount[0], int(coin_accuracy))
        if all_amount[1] is None or all_amount[1] == 0:
            all_dividend_water = 0
        else:
            all_dividend_water = normalize_fraction(all_amount[1], int(coin_accuracy))
        nowadays = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
        nowadays_start = str(nowadays) + ' 00:00:00'
        nowadays_end = str(nowadays) + ' 23:59:59'
        sql = "select sum(pu.bet_water), sum(pu.dividend_water) from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(nowadays_start) + "'"
        sql += " and pu.created_at <= '" + str(nowadays_end) + "'"
        nowadays_amount = get_sql(sql)[0]
        if nowadays_amount[0] is None or nowadays_amount[0] == 0:
            nowadays_bet_water = 0
        else:
            nowadays_bet_water = normalize_fraction(nowadays_amount[0], int(coin_accuracy))
        if nowadays_amount[1] is None or nowadays_amount[1] == 0:
            nowadays_dividend_water = 0
        else:
            nowadays_dividend_water = normalize_fraction(nowadays_amount[1], int(coin_accuracy))
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_start = str(yesterday) + ' 00:00:00'
        yesterday_end = str(yesterday) + ' 23:59:59'
        sql = "select sum(pu.bet_water), sum(pu.dividend_water) from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(yesterday_start) + "'"
        sql += " and pu.created_at <= '" + str(yesterday_end) + "'"
        yesterday_amount = get_sql(sql)[0]
        if yesterday_amount[0] is None or yesterday_amount[0] == 0:
            yesterday_bet_water = 0
        else:
            yesterday_bet_water = normalize_fraction(yesterday_amount[0], int(coin_accuracy))
        if yesterday_amount[1] is None or yesterday_amount[1] == 0:
            yesterday_dividend_water = 0
        else:
            yesterday_dividend_water = normalize_fraction(yesterday_amount[1], int(coin_accuracy))

        sql = "select DATE_FORMAT(pm.created_at,'%Y年%m月')months, pm.income, pm.income_dividend, pm.proportion from promotion_presentationmonth pm"
        sql += " where pm.club_id = '" + str(club_id) + "'"
        sql += " and pm.user_id = '" + str(user.id) + "'"
        amount_list = get_sql(sql)
        month_list = []
        sum_coin = Decimal(all_dividend_water)
        for i in amount_list:
            sum_coin += Decimal(i[2])
            month_list.append({
                "months": i[0],
                "income": normalize_fraction(i[1], int(coin_accuracy)),
                "income_dividend": normalize_fraction(i[2], int(coin_accuracy)),
                "proportion": normalize_fraction(i[3], int(coin_accuracy))
            })
        sum_coin = normalize_fraction(sum_coin, int(coin_accuracy))

        return self.response({'code': 0, 'data': {
            "coin_icon": coin_icon,
            "sum_coin": sum_coin,
            "all_bet_water": all_bet_water,
            "all_dividend_water": all_dividend_water,
            "nowadays_bet_water": nowadays_bet_water,
            "nowadays_dividend_water": nowadays_dividend_water,
            "yesterday_bet_water": yesterday_bet_water,
            "yesterday_dividend_water": yesterday_dividend_water,
        }, "month_list": month_list})


class ClubRuleView(ListAPIView):
    """
    玩法列表
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        sql = "select name from quiz_category"
        sql += " where id in (1, 2)"
        quiz_rule = get_sql(sql)
        data = []
        for s in quiz_rule:
            if s[0] == "篮球":
                number = 2
            else:
                number = 3
            data.append({
                "name": s[0],
                "number": number
            })

        sql = "select title from chat_clubrule"
        sql += " where id > 1"
        club_rule_info = get_sql(sql)
        for i in club_rule_info:
            if i[0] == "猜股指":
                number = 4
            elif i[0] == "六合彩":
                number = 5
            elif i[0] == "龙虎斗":
                number = 6
            elif i[0] == "百家乐":
                number = 7
            else:
                number = 7+1
            data.append({
                "name": i[0],
                "number": number
            })

        return self.response({'code': 0, "data":data})


class ClubDetailView(ListAPIView):
    """
    流水明细
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = self.request.GET.get('club_id')
        if int(club_id) == 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        sql = "select u.coin_accuracy, u.name from chat_club c"
        sql += " inner join users_coin u on c.coin_id=u.id"
        sql += " where c.id = '" + str(club_id) + "'"
        club_info = get_sql(sql)[0]
        coin_accuracy = club_info[0]
        coin_name = club_info[1]

        if 'time_type' in self.request.GET:
            time_type = str(self.request.GET.get('time_type'))
            regex = re.compile(r'^(1|2|3|4)$')  # 1.今天 2.昨天 3.今月 4. 上月
            if time_type is None or not regex.match(time_type):
                raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

            if int(time_type) == 1:  # 今天
                created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
                start_time = str(created_at_day) + ' 00:00:00'  # 一天开始时间
                end_time = str(created_at_day) + ' 23:59:59'  # 一天结束时间
            elif int(time_type) == 2:  # 昨天
                yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                start_time = str(yesterday) + ' 00:00:00'
                end_time = str(yesterday) + ' 23:59:59'
            elif int(time_type) == 3:  # 当月
                year = datetime.date.today().year  # 获取当前年份
                month = datetime.date.today().month  # 获取当前月份
                weekDay, monthCountDay = calendar.monthrange(year, month)  # 获取当月第一天的星期和当月的总天数
                start = datetime.date(year, month, day=1).strftime('%Y-%m-%d')  # 获取当月第一天
                end = datetime.date(year, month, day=monthCountDay).strftime('%Y-%m-%d')  # 获取当前月份最后一天
                start_time = str(start) + ' 00:00:00'
                end_time = str(end) + ' 23:59:59'
            else:  # 上月
                this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
                end = this_month_start - timedelta(days=1)  # 上个月的最后一天
                start_time = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
                end_time = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'
        else:
            if 'start_time' in self.request.GET:
                start_time = self.request.GET.get('start_time')
                start_time = str(start_time) + ' 00:00:00'
            else:
                start_time = str(settings.PROMOTER_EXCHANGE_START_DATE) + ' 00:00:00'
            if 'end_time' in self.request.GET:
                end_time = self.request.GET.get('end_time')
                end_time = str(end_time) + ' 23:59:59'
            else:
                enddays = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
                end_time = str(enddays) + ' 23:59:59'


        type = str(self.request.GET.get('type'))
        regex = re.compile(r'^(1|2|3|4|5|6|7)$')  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        sql = "select ui.invitee_one from users_userinvitation ui"
        sql += " where ui.inviter_id = '" + str(user.id) + "'"
        sql += " and ui.invitee_one != 0"
        sql += " and ui.inviter_type != 2"
        invitee_id_list = get_sql(sql)
        invite_number = len(invitee_id_list)
        user_id_list = []
        for i in invitee_id_list:
            user_id_list.append(str(i[0]))

        sql = "select sum(pu.bet_water), sum(pu.dividend_water) from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(start_time) + "'"
        sql += " and pu.created_at <= '" + str(end_time) + "'"
        yesterday_amount = get_sql(sql)[0]
        if yesterday_amount[0] == None:
            bet_water = str(0) + " " + coin_name
            dividend_water = str(0) + " " + coin_name
        else:
            bet_water = str(normalize_fraction(yesterday_amount[0], coin_accuracy)) + " " + coin_name
            dividend_water = str(normalize_fraction(yesterday_amount[1], coin_accuracy)) + " " + coin_name

        data_list = []
        if int(type) == 1:   # 1.全部
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '猜股指' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from guess_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)   # 股票
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
            sql_list = "sum(dtr.bet_coin), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '六合彩' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from marksix_sixrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            marksix_list = self.get_list_by_sql(sql)      # 六合彩
            for i in marksix_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '龙虎斗' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            baccarat_list = self.get_list_by_sql(sql)   # 百家乐
            for i in baccarat_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status,  '百家乐' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            dragontiger_list = self.get_list_by_sql(sql)   # 龙虎斗
            for i in dragontiger_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.type, '足球' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            basketball_list = self.get_list_by_sql(sql)   # 篮球
            for i in basketball_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.type, '足球' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 2"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            football_list = self.get_list_by_sql(sql)       # 足球
            for i in football_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        elif int(type) == 2:       # 2. 篮球
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.type, '足球' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        elif int(type) == 3:     # 3.足球
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.type, '足球' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 2"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        elif int(type) == 4: # 4. 股票
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '猜股指' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from guess_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        elif int(type) == 5:  # 5. 六合彩
            sql_list = "sum(dtr.bet_coin), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '六合彩' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from marksix_sixrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        elif int(type) == 7:       # 百家乐
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status, '龙虎斗' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        else:        # 龙虎斗
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years, date_format( dtr.created_at, '%k:%i' ) as time,"
            sql_list += " date_format( dtr.created_at, '%Y%c%e%k%i' ) AS created_ats, dtr.status,  '百家乐' as rule, u.nickname, u.avatar"
            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            sql += " group by dtr.user_id, yearss, years, time, created_ats, u.nickname, u.avatar, rule"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                data_list.append({
                    "bets": normalize_fraction(i[0], coin_accuracy),
                    "yearss": i[1],
                    "years": i[2],
                    "time": i[3],
                    "created_ats": i[4],
                    "status": i[5],
                    "rule": i[6],
                    "nickname": i[7],
                    "avatar": i[8]
                })
        data_one_list = sorted(data_list, key=lambda x: x['created_ats'], reverse = True)
        data = []
        tmps = ''
        tmp = ''
        for fav in data_one_list:
            if int(fav["status"]) == 0:
                status = "待结算"
                if self.request.GET.get('language') == 'en':
                    status = "Pending settlement"
            elif fav["rule"] not in ["篮球", "足球"] and int(fav["status"]) == 2:
                status = "流盘"
                if self.request.GET.get('language') == 'en':
                    status = "Flow disk"
            elif fav["rule"] in ["篮球", "足球"] and int(fav["status"]) == 3:
                status = "流盘"
                if self.request.GET.get('language') == 'en':
                    status = "Flow disk"
            else:
                status = "已结算"
                if self.request.GET.get('language') == 'en':
                    status = "Settled"

            divided_into = fav["bets"] * Decimal(0.005)
            divided_into = "+ " + str(normalize_fraction(divided_into, coin_accuracy)) + " " + coin_name


            pecific_dates = fav["years"]
            pecific_date = fav["time"]
            if tmps == pecific_dates:
                pecific_dates = ""
                if tmp == pecific_date:
                    pecific_date = ""
                else:
                    tmp = pecific_date
            else:
                tmps = pecific_dates
                if tmp == pecific_date:
                    pecific_date = ""
                else:
                    tmp = pecific_date
            data.append({
                "status": status,
                "divided_into": divided_into,
                "nickname": fav["nickname"],
                "avatar": fav["avatar"],
                "bets": fav["bets"],
                "rule": fav["rule"],
                "pecific_dates": pecific_dates,
                "pecific_date": pecific_date,
            })
        return self.response({'code': 0,
                              "invite_number": invite_number,
                              "bet_water": bet_water,
                              "dividend_water": dividend_water,
                              "data": data
                              })


class ClubDividendView(ListAPIView):
    """
    分成明细
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = self.request.GET.get('club_id')        # 俱乐部ID
        if int(club_id) == 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        sql = "select u.coin_accuracy, u.name from chat_club c"
        sql += " inner join users_coin u on c.coin_id=u.id"
        sql += " where c.id = '" + str(club_id) + "'"
        club_info = get_sql(sql)[0]
        coin_accuracy = club_info[0]    # 货币精度
        coin_name = club_info[1]        # 货币昵称

        type = str(self.request.GET.get('type'))
        regex = re.compile(r'^(1|2|3|4|5|6|7)$')  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

        if 'time_type' in self.request.GET:
            time_type = str(self.request.GET.get('time_type'))
            regex = re.compile(r'^(1|2|3|4)$')  # 1.今天 2.昨天 3.今月 4. 上月
            if time_type is None or not regex.match(time_type):
                raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

            if int(time_type) == 1:  # 今天
                created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
                start_year = datetime.datetime.now().year
                start_month = datetime.datetime.now().month
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month
                start_time = str(created_at_day) + ' 00:00:00'  # 一天开始时间
                end_time = str(created_at_day) + ' 23:59:59'  # 一天结束时间
            elif int(time_type) == 2:  # 昨天
                yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                start_year = datetime.datetime.now().year
                start_month = datetime.datetime.now().month
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month
                start_time = str(yesterday) + ' 00:00:00'
                end_time = str(yesterday) + ' 23:59:59'
            elif int(time_type) == 3:  # 当月
                year = datetime.date.today().year  # 获取当前年份
                month = datetime.date.today().month  # 获取当前月份
                weekDay, monthCountDay = calendar.monthrange(year, month)  # 获取当月第一天的星期和当月的总天数
                start = datetime.date(year, month, day=1).strftime('%Y-%m-%d')  # 获取当月第一天
                end = datetime.date(year, month, day=monthCountDay).strftime('%Y-%m-%d')  # 获取当前月份最后一天
                start_year = datetime.datetime.now().year
                start_month = datetime.datetime.now().month
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month
                start_time = str(start) + ' 00:00:00'
                end_time = str(end) + ' 23:59:59'
            else:  # 上月
                this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
                end = this_month_start - timedelta(days=1)  # 上个月的最后一天
                start_time = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
                end_time = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'
                start_year = datetime.datetime(end.year, end.month, 1).year
                start_month = datetime.datetime(end.year, end.month, 1).month
                end_year = datetime.datetime(end.year, end.month, 1).year
                end_month = datetime.datetime(end.year, end.month, 1).month
        else:
            # 开始时间
            if 'start_day' in self.request.GET:  # 用户选择的开始时间
                start_day = self.request.GET.get('start_day')
                start_time = str(start_day) + ' 00:00:00'
                start_day_test = datetime.datetime.strptime(start_day, "%Y-%m-%d")
                start_year = start_day_test.year
                start_month = start_day_test.month
            else:  # 默认开始时间
                start_day = settings.PROMOTER_EXCHANGE_START_DATE
                start_time = str(start_day) + ' 00:00:00'
                start_day_test = datetime.datetime.strptime(start_day, "%Y-%m-%d")
                start_year = start_day_test.year
                start_month = start_day_test.month

            # 结束时间
            if 'end_day' in self.request.GET:  # 用户选择的结束时间
                end_day = self.request.GET.get('end_day')
                end_time = str(end_day) + ' 23:59:59'
                end_day_test = datetime.datetime.strptime(end_day, "%Y-%m-%d")
                end_year = end_day_test.year
                end_month = end_day_test.month
            else:  # 默认日期  当天结束时间
                end_day = datetime.datetime.now().strftime('%Y-%m-%d')
                end_time = str(end_day) + ' 23:59:59'
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month

        if start_year == end_year and start_month == end_month:
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            if current_year == 1:   # 获取上个月的年份
                last_month_year = current_year-1
            else:
                last_month_year = current_year
            last_month_month = current_month-1 or 12    # 获取上个月的月份

            if last_month_year == end_year and last_month_month == end_month:
                this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
                end = this_month_start - timedelta(days=1)  # 上个月的最后一天
                start = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
                end = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'
            else:
                start_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month
                weekDay, monthCountDay = calendar.monthrange(start_year, end_month)  # 当月第一天的星期 当月的总天数
                month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
                start = str(month_first_day) + ' 00:00:00'  # 本月第一天
                end = datetime.date(year=start_year, month=end_month, day=monthCountDay).strftime(
                    '%Y-%m-%d')+ ' 23:59:59'  # 当月最后一天
        else:
            start_year = datetime.datetime.now().year
            end_month = datetime.datetime.now().month
            weekDay, monthCountDay = calendar.monthrange(start_year, end_month)  # 当月第一天的星期 当月的总天数
            month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
            start = str(month_first_day) + ' 00:00:00'  # 本月第一天
            end = datetime.date(year=start_year, month=end_month, day=monthCountDay).strftime(
                '%Y-%m-%d') + ' 23:59:59'  # 当月最后一天

        sql = "select date_format( pu.created_at, '%Y%m' ) AS created_ats, sum(pu.income) from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(start) + "'"
        sql += " and pu.created_at <= '" + str(end) + "'"
        the_month_list = get_sql(sql)
        month_list = {}
        if the_month_list[0][1] == None:
            the_month_income_sum = 0
            the_month_income_proportion = reward_gradient(user.id, club_id, the_month_income_sum)  # 本月兑换比例比例
            month_list[datetime.datetime.now().strftime('%Y%m')] = {
                "months": datetime.datetime.now().strftime('%Y%m'),
                "proportion": 0
            }
        else:
            the_month_income_sum = normalize_fraction(the_month_list[0][1], coin_accuracy)
            the_month_income_proportion = reward_gradient(user.id, club_id, the_month_income_sum)  # 本月兑换比例比例
            month_list[the_month_list[0][0]] = {
                "months": the_month_list[0][0],
                "proportion": the_month_income_proportion
            }


        sql_list = "date_format( pm.created_at, '%Y%m' ) AS created_ats, pm.proportion"
        sql = "select " + sql_list + " from promotion_presentationmonth pm"
        sql += " where pm.club_id = '" + str(club_id) + "'"
        sql += " and pm.user_id = '" + str(user.id) + "'"
        sql += " and pm.created_at >= '" + str(start_time) + "'"
        sql += " and pm.created_at <= '" + str(end_time) + "'"
        amount_list = get_sql(sql)

        for i in amount_list:
            month_list[i[0]]={
                "months": i[0],
                "proportion": normalize_fraction(i[1], int(coin_accuracy))
            }
        sql = "select ui.invitee_one from users_userinvitation ui"
        sql += " where ui.inviter_id = '" + str(user.id) + "'"
        sql += " and ui.invitee_one != 0"
        sql += " and ui.inviter_type != 2"
        invitee_id_list = get_sql(sql)
        user_id_list = []
        for i in invitee_id_list:
            user_id_list.append(str(i[0]))

        user_list = {}
        data_list = []
        if int(type) == 1:  # 1.全部
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '猜股指' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from guess_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            print("sql=============================", sql)
            record_list = self.get_list_by_sql(sql)  # 股票
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
            sql_list = "sum(dtr.bet_coin), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '六合彩' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from marksix_sixrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            marksix_list = self.get_list_by_sql(sql)  # 六合彩
            for i in marksix_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '龙虎斗' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            baccarat_list = self.get_list_by_sql(sql)  # 百家乐
            for i in baccarat_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '百家乐' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            dragontiger_list = self.get_list_by_sql(sql)  # 龙虎斗
            for i in dragontiger_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '足球' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 1"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.type in (1, 2)"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            basketball_list = self.get_list_by_sql(sql)  # 篮球
            for i in basketball_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '足球' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 2"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.type in (1, 2)"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            football_list = self.get_list_by_sql(sql)  # 足球
            for i in football_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        elif int(type) == 2:  # 2. 篮球
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '足球' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 1"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.type in (1, 2)"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        elif int(type) == 3:  # 3.足球
            sql_list = "sum(dtr.bet), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '足球' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " inner join quiz_quiz q on dtr.quiz_id=q.id"
            sql += " inner join quiz_category c on q.category_id=c.id"
            sql += " where dtr.roomquiz_id = '" + club_id + "'"
            sql += " and c.parent_id = 2"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.type in (1, 2)"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        elif int(type) == 4:  # 4. 股票
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '猜股指' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from guess_record dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        elif int(type) == 5:  # 5. 六合彩
            sql_list = "sum(dtr.bet_coin), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '六合彩' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats,dtr.user_id"
            sql = "select " + sql_list + " from marksix_sixrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        elif int(type) == 7:  # 百家乐
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '龙虎斗' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        else:  # 龙虎斗
            sql_list = "sum(dtr.bets), date_format( dtr.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( dtr.created_at, '%c/%e' ) as years,"
            sql_list += " '百家乐' as rule, u.nickname, u.avatar, sum(dtr.earn_coin),"
            sql_list += " date_format( dtr.created_at, '%Y%m%d' ) AS created_ats, dtr.user_id"
            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.club_id = '" + club_id + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(end_time) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.created_at > '2018-09-07 00:00:00'"
            if user_id_list != []:
                sql += " and dtr.user_id in (" + ','.join(user_id_list) + ")"
            sql += " group by dtr.user_id, yearss, years, u.nickname, u.avatar, rule, created_ats"
            sql += " order by created_ats desc"
            record_list = self.get_list_by_sql(sql)
            for i in record_list:
                if i[8] not in user_list:
                    user_list[i[8]] = i[8]
                data_list.append({
                    "bets": Decimal(i[0]),
                    "earn_coin": Decimal(i[6]),
                    "yearss": i[1],
                    "years": i[2],
                    "rule": i[3],
                    "nickname": i[4],
                    "avatar": i[5],
                    "created_ats": i[7]
                })
        data_one_list = sorted(data_list, key=lambda x: x['created_ats'], reverse=True)

        data = []
        tmps = ''
        tmp = ''
        for fav in data_one_list:
            if fav["created_ats"] in month_list:
                proportion = Decimal(month_list[fav["created_ats"]]["proportion"])
            else:
                proportion = 0

            if fav["earn_coin"] > 0:
                reward_coin = fav["earn_coin"] - fav["bets"]
            else:
                reward_coin = fav["earn_coin"]

            dividend = normalize_fraction((opposite_number(reward_coin) * proportion), coin_accuracy)

            # if Decimal(dividend) > 0:
            #     dividend = "+ " + str(dividend) + " " + coin_name
            # else:
            #     dividend = " " + str(dividend) + " " + coin_name

            pecific_dates = fav["yearss"]
            pecific_date = fav["years"]
            if tmps == pecific_dates:
                pecific_dates = ""
                if tmp == pecific_date:
                    pecific_date = ""
                else:
                    tmp = pecific_date
            else:
                tmps = pecific_dates
                if tmp == pecific_date:
                    pecific_date = ""
                else:
                    tmp = pecific_date
            data.append({
                "nickname": fav["nickname"],
                "avatar": fav["avatar"],
                "bets": normalize_fraction(fav["bets"], coin_accuracy),
                "reward_coin": normalize_fraction(reward_coin, coin_accuracy),
                "dividend": dividend,
                "rule": fav["rule"],
                "pecific_dates": pecific_dates,
                "pecific_date": pecific_date,
            })

        return self.response({'code': 0,
                              "the_month_income_sum": the_month_income_sum,
                              "the_month_user_number": len(user_list),
                              "the_month_income_proportion": the_month_income_proportion,
                              "data": data
                              })


class CustomerView(ListAPIView):
    """
    我的客人
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if 'start_time' in self.request.GET:
            start_time = self.request.GET.get('start_time')
            start_time = str(start_time) + ' 00:00:00'
        else:
            start_time = str(settings.PROMOTER_EXCHANGE_START_DATE) + ' 00:00:00'    # 开始时间

        if 'end_time' in self.request.GET:
            end_time = self.request.GET.get('end_time')
            end_time = str(end_time) + ' 23:59:59'
        else:
            enddays = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = str(enddays) + ' 23:59:59' # 结束时间

        if 'type' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        type = self.request.GET.get('type')
        regex = re.compile(r'^(1|2)$')  # 1.注册时间   2. 登录时间
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)

        user_list = {}
        if int(type) == 1:
            sql_list = "ui.invitee_one, u.avatar, u.nickname, u.created_at, ui.inviter_type,"
            sql_list += " (select l.login_time from users_loginrecord l where " \
                        "l.user_id=ui.invitee_one order by l.login_time desc limit 1) as login_time"
            sql = "select " + sql_list + " from users_userinvitation ui"
            sql += " inner join users_user u on ui.invitee_one=u.id"
            sql += " where ui.invitee_one != 0"
            sql += " and ui.inviter_id = '" + str(user.id) + "'"
            sql += " and ui.created_at >= '" + str(start_time) + "'"
            sql += " and ui.created_at <= '" + str(end_time) + "'"
            if "name" in self.request.GET:
                name = self.request.GET.get('name')
                name_now = "%" + str(name) + "%"
                sql += " and (u.nickname like '" + name_now + "'"
                sql += " or u.username = '" + str(name) + "')"
            sql += " group by ui.invitee_one"
            sql += " order by login_time desc"
            invitee_list = self.get_list_by_sql(sql)
            data = []
            for i in invitee_list:
                coin_info = ""
                if int(i[4]) == 1:
                    coin_info = "+ 5 GSG"
                user_list[i[0]] = i[0]
                data.append({
                    "user_id": i[0],
                    "avatar": i[1],
                    "nickname": i[2],
                    "created_at": i[3].strftime('%Y-%m-%d %H:%M'),
                    "coin_info": coin_info,
                    "login_time": i[5].strftime('%Y-%m-%d %H:%M')
                })
        else:
            sql_list = "l.user_id, u.avatar, u.nickname, u.created_at,"
            sql_list += " (select ui.invitee_one from users_userinvitation ui " \
                        "where ui.invitee_one = l.user_id and ui.inviter_id = '" + str(user.id) + \
                        "') as inviter_type, l.login_time"
            sql = "select " + sql_list + " from users_loginrecord l"
            sql += " inner join users_user u on l.user_id=u.id"
            sql += " and l.login_time >= '" + str(start_time) + "'"
            sql += " and l.login_time <= '" + str(end_time) + "'"
            sql += " and l.user_id in (select ui.invitee_one from users_userinvitation ui " \
                   "where ui.invitee_one != 0 and ui.inviter_id = '" + str(user.id) + "')"
            if "name" in self.request.GET:
                name = self.request.GET.get('name')
                name_now = "%" + str(name) + "%"
                sql += " and (u.nickname like '" + name_now + "'"
                sql += " or u.username = '" + str(name) + "')"
            # sql += " group by ui.invitee_one"
            sql += " order by l.login_time desc"
            invitee_list = self.get_list_by_sql(sql)
            data = []
            for i in invitee_list:
                coin_info = ""
                if int(i[4])==1:
                    coin_info = "+ 5 GSG"
                user_list[i[0]] = i[0]
                data.append({
                    "user_id": i[0],
                    "avatar": i[1],
                    "nickname": i[2],
                    "created_at": i[3].strftime('%Y-%m-%d %H:%M'),
                    "coin_info": coin_info,
                    "login_time": i[5].strftime('%Y-%m-%d %H:%M')
                })
        user_number = len(user_list)
        return self.response({'code': 0, "user_number":user_number, "data":data})


class UserInfoView(ListAPIView):
    """
    用户详情
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        return

    def list(self, request, *args, **kwargs):
        user = self.request.user
        if 'invitee_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        invitee_id = self.request.GET.get('invitee_id')

        sql_list = " u.avatar, u.nickname, u.created_at, (select l.login_time from users_loginrecord l where " \
                   "l.user_id=u.id order by l.login_time desc limit 1) as login_time"
        sql = "select " + sql_list + " from users_user u"
        sql += " where u.id = '" + str(invitee_id) + "'"
        user_infos = get_sql(sql)[0]
        if user_infos == ():
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_info = {
            "avatar":user_infos[0],
            "nickname":user_infos[1],
            "created_at":user_infos[2].strftime('%Y-%m-%d %H:%M'),
            "login_time":user_infos[3].strftime('%Y-%m-%d %H:%M')
        }

        coin_id_list = []
        all_club = Club.objects.filter(~Q(pk=1))
        club_list = {}
        coins = Coin.objects.get_all()
        map_coin = {}
        for coin in coins:
            map_coin[coin.id] = coin
        for i in all_club:
            coin_id_list.append(str(i.id))
            coin = map_coin[i.coin.id]
            club_list[i.id] = {
                "club_id": i.id,
                "coin_id": coin.id,
                "coin_icon": coin.icon,
                "coin_name": coin.name,
                "coin_accuracy": coin.coin_accuracy
            }

        start_time = str(settings.PROMOTER_EXCHANGE_START_DATE) + ' 00:00:00'          # 活动开始时间
        enddays = datetime.datetime.now().strftime('%Y-%m-%d')
        end_time = str(enddays) + ' 23:59:59'  # 当前时间


        start_year = datetime.datetime.now().year
        end_month = datetime.datetime.now().month
        month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
        if int(end_month)-1 == 0:
            before_month = 12
            before_yeas = int(start_year) - 1
            weekDay, monthCountDay = calendar.monthrange(before_yeas, before_month)
            before_first_day = datetime.date(before_yeas, before_month, day=monthCountDay).strftime('%Y-%m-%d')
            before_start = str(before_first_day) + ' 00:00:00'  # 本月第一天
        else:
            before_month = int(end_month) - 1
            before_yeas = int(start_year) - 1
            weekDay, monthCountDay = calendar.monthrange(before_yeas, before_month)
            before_first_day = datetime.date(before_yeas, before_month, day=monthCountDay).strftime('%Y-%m-%d')
            before_start = str(before_first_day) + ' 00:00:00'  # 本月第一天
        start = str(month_first_day) + ' 00:00:00'  # 本月第一天

        data_list = {}
        if start != start_time:
            sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
            sql = "select " + sql_list + " from guess_record dtr"
            sql += " where dtr.user_id = '" + str(invitee_id) + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(before_start) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by dtr.club_id, created_ats"
            sql += " order by dtr.club_id desc"
            before_record_list = get_sql(sql)  # 股票
            for i in before_record_list:
                data_list[i[0]][i[2]] = {
                    "bets": i[1],
                    "earn_coin": i[3]
                }

            sql_list = "dtr.club_id, sum(dtr.bet_coin), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bet_coin ELSE dtr.earn_coin END)) AS earn_coin"
            sql = "select " + sql_list + " from marksix_sixrecord dtr"
            sql += " inner join users_user u on dtr.user_id=u.id"
            sql += " where dtr.user_id = '" + str(invitee_id) + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(before_start) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by dtr.club_id, created_ats"
            sql += " order by dtr.club_id desc"
            marksix_list = get_sql(sql)  # 六合彩
            for s in marksix_list:
                if s[0] not in data_list:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }
                else:
                    if s[2] in data_list[s[0]]:
                        data_list[s[0]][s[2]]["bets"] += s[1]
                        data_list[s[0]][s[2]]["earn_coin"] += s[3]
                    else:
                        data_list[s[0]] = {
                            s[2]: {
                                "bets": s[1],
                                "earn_coin": s[3]
                            }
                        }

            sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
            sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
            sql += " where dtr.user_id = '" + str(invitee_id) + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(before_start) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by dtr.club_id, created_ats"
            sql += " order by dtr.club_id desc"
            baccarat_list = get_sql(sql)  # 百家乐
            for s in baccarat_list:
                if s[0] not in data_list:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }
                else:
                    if s[2] in data_list[s[0]]:
                        data_list[s[0]][s[2]]["bets"] += s[1]
                        data_list[s[0]][s[2]]["earn_coin"] += s[3]
                    else:
                        data_list[s[0]] = {
                            s[2]: {
                                "bets": s[1],
                                "earn_coin": s[3]
                            }
                        }

            sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
            sql += " where dtr.user_id = '" + str(invitee_id) + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(before_start) + "'"
            sql += " and dtr.status = 1"
            sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by dtr.club_id, created_ats"
            sql += " order by dtr.club_id desc"
            dragontiger_list = get_sql(sql)  # 龙虎斗
            for s in dragontiger_list:
                if s[0] not in data_list:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }
                else:
                    if s[2] in data_list[s[0]]:
                        data_list[s[0]][s[2]]["bets"] += s[1]
                        data_list[s[0]][s[2]]["earn_coin"] += s[3]
                    else:
                        data_list[s[0]] = {
                            s[2]: {
                                "bets": s[1],
                                "earn_coin": s[3]
                            }
                        }

            sql_list = "dtr.roomquiz_id, sum(dtr.bet), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bet ELSE dtr.earn_coin END)) AS earn_coin"
            sql = "select " + sql_list + " from quiz_record dtr"
            sql += " where dtr.user_id = '" + str(invitee_id) + "'"
            sql += " and dtr.created_at >= '" + str(start_time) + "'"
            sql += " and dtr.created_at <= '" + str(before_start) + "'"
            sql += " and dtr.type in (1, 2)"
            sql += " and dtr.roomquiz_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by dtr.roomquiz_id, created_ats"
            sql += " order by dtr.roomquiz_id desc"
            quiz_list = self.get_list_by_sql(sql)  # 篮球
            for s in quiz_list:
                if s[0] not in data_list:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }
                else:
                    if s[2] in data_list[s[0]]:
                        data_list[s[0]][s[2]]["bets"] += s[1]
                        data_list[s[0]][s[2]]["earn_coin"] += s[3]
                    else:
                        data_list[s[0]] = {
                            s[2]: {
                                "bets": s[1],
                                "earn_coin": s[3]
                            }
                        }

        sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
        sql = "select " + sql_list + " from guess_record dtr"
        sql += " where dtr.user_id = '" + str(invitee_id) + "'"
        sql += " and dtr.created_at >= '" + str(start) + "'"
        sql += " and dtr.created_at <= '" + str(end_time) + "'"
        sql += " and dtr.status = 1"
        sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by dtr.club_id"
        sql += " order by dtr.club_id desc"
        before_record_list = get_sql(sql)  # 股票
        for s in before_record_list:
            if s[0] not in data_list:
                data_list[s[0]] = {
                    s[2]: {
                        "bets": s[1],
                        "earn_coin": s[3]
                    }
                }
            else:
                if s[2] in data_list[s[0]]:
                    data_list[s[0]][s[2]]["bets"] += s[1]
                    data_list[s[0]][s[2]]["earn_coin"] += s[3]
                else:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }

        sql_list = "dtr.club_id, sum(dtr.bet_coin), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bet_coin ELSE dtr.earn_coin END)) AS earn_coin"
        sql = "select " + sql_list + " from marksix_sixrecord dtr"
        sql += " inner join users_user u on dtr.user_id=u.id"
        sql += " where dtr.user_id = '" + str(invitee_id) + "'"
        sql += " and dtr.created_at >= '" + str(start) + "'"
        sql += " and dtr.created_at <= '" + str(end_time) + "'"
        sql += " and dtr.status = 1"
        sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by dtr.club_id"
        sql += " order by dtr.club_id desc"
        marksix_list = get_sql(sql)  # 六合彩
        for s in marksix_list:
            if s[0] not in data_list:
                data_list[s[0]] = {
                    s[2]: {
                        "bets": s[1],
                        "earn_coin": s[3]
                    }
                }
            else:
                if s[2] in data_list[s[0]]:
                    data_list[s[0]][s[2]]["bets"] += s[1]
                    data_list[s[0]][s[2]]["earn_coin"] += s[3]
                else:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }

        sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
        sql = "select " + sql_list + " from baccarat_baccaratrecord dtr"
        sql += " where dtr.user_id = '" + str(invitee_id) + "'"
        sql += " and dtr.created_at >= '" + str(start) + "'"
        sql += " and dtr.created_at <= '" + str(end_time) + "'"
        sql += " and dtr.status = 1"
        sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by dtr.club_id"
        sql += " order by dtr.club_id desc"
        baccarat_list = get_sql(sql)  # 百家乐
        for s in baccarat_list:
            if s[0] not in data_list:
                data_list[s[0]] = {
                    s[2]: {
                        "bets": s[1],
                        "earn_coin": s[3]
                    }
                }
            else:
                if s[2] in data_list[s[0]]:
                    data_list[s[0]][s[2]]["bets"] += s[1]
                    data_list[s[0]][s[2]]["earn_coin"] += s[3]
                else:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }

        sql_list = "dtr.club_id, sum(dtr.bets), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bets ELSE dtr.earn_coin END)) AS earn_coin"
        sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord dtr"
        sql += " where dtr.user_id = '" + str(invitee_id) + "'"
        sql += " and dtr.created_at >= '" + str(start) + "'"
        sql += " and dtr.created_at <= '" + str(end_time) + "'"
        sql += " and dtr.status = 1"
        sql += " and dtr.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by dtr.club_id"
        sql += " order by dtr.club_id desc"
        dragontiger_list = get_sql(sql)  # 龙虎斗
        for s in dragontiger_list:
            if s[0] not in data_list:
                data_list[s[0]] = {
                    s[2]: {
                        "bets": s[1],
                        "earn_coin": s[3]
                    }
                }
            else:
                if s[2] in data_list[s[0]]:
                    data_list[s[0]][s[2]]["bets"] += s[1]
                    data_list[s[0]][s[2]]["earn_coin"] += s[3]
                else:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }

        sql_list = "dtr.roomquiz_id, sum(dtr.bet), date_format( dtr.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN dtr.earn_coin > 0 THEN dtr.earn_coin - dtr.bet ELSE dtr.earn_coin END)) AS earn_coin"
        sql = "select " + sql_list + " from quiz_record dtr"
        sql += " where dtr.user_id = '" + str(invitee_id) + "'"
        sql += " and dtr.created_at >= '" + str(start) + "'"
        sql += " and dtr.created_at <= '" + str(end_time) + "'"
        sql += " and dtr.type in (1, 2)"
        sql += " and dtr.roomquiz_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by dtr.roomquiz_id"
        sql += " order by dtr.roomquiz_id desc"
        quiz_list = self.get_list_by_sql(sql)  # 篮球
        for s in quiz_list:
            if s[0] not in data_list:
                data_list[s[0]] = {
                    s[2]: {
                        "bets": s[1],
                        "earn_coin": s[3]
                    }
                }
            else:
                if s[2] in data_list[s[0]]:
                    data_list[s[0]][s[2]]["bets"] += s[1]
                    data_list[s[0]][s[2]]["earn_coin"] += s[3]
                else:
                    data_list[s[0]] = {
                        s[2]: {
                            "bets": s[1],
                            "earn_coin": s[3]
                        }
                    }
        data = []
        for i in club_list:
            coin_accuracy = club_list[i]["coin_accuracy"]
            club_id = club_list[i]["club_id"]
            coin_name = club_list[i]["coin_name"]
            coin_name = club_list[i]["coin_name"]
            coin_icon = club_list[i]["coin_icon"]
            sum_bet = 0
            sum_bet_water = 0
            sum_income = 0
            sum_income_water = 0
            if club_id in data_list:
                for s in data_list[club_id]:
                    sum_bet += normalize_fraction(data_list[club_id][s]["bets"], int(coin_accuracy))
                    income = normalize_fraction(data_list[club_id][s]["earn_coin"], int(coin_accuracy))
                    income_dividend = reward_gradient_all(club_id, income)
                    sum_income += income
                    sum_income_water += Decimal(income_dividend) * Decimal(income)
                sum_bet_water = sum_bet * Decimal(0.005)
            data.append({
                "coin_name": coin_name,
                "coin_icon": coin_icon,
                "sum_bet": sum_bet,
                "sum_bet_water": normalize_fraction(sum_bet_water, int(coin_accuracy)),
                "sum_income": sum_income,
                "sum_income_water": normalize_fraction(sum_income_water, int(coin_accuracy))
            })


        return self.response({'code': 0, "user_info": user_info, "data": data})