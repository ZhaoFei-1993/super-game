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
from utils.functions import normalize_fraction, value_judge, get_sql, reward_gradient, opposite_number, \
    reward_gradient_all, to_decimal
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
        nowadays_old = str(nowadays_day) + ' 23:59:59'
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_now = str(yesterday) + ' 00:00:00'
        yesterday_old = str(yesterday) + ' 23:59:59'

        user_avatar = user.avatar  # 用户头像
        nowadays_number = UserInvitation.objects.filter(Q(created_at__lte=nowadays_old),
                                                        Q(created_at__gte=nowadays_now),
                                                        inviter_id=user.id).count()  # 今天邀请人数
        yesterday_number = UserInvitation.objects.filter(Q(created_at__lte=yesterday_old),
                                                         Q(created_at__gte=yesterday_now),
                                                         inviter_id=user.id).count()  # 昨天邀请人数
        all_user_number = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1).count()  # 总邀请人数
        all_user_gsg = UserInvitation.objects.filter(inviter_id=user.id, inviter_type=1, status=2).aggregate(
            Sum('money'))
        sum_gsg = all_user_gsg['money__sum'] if all_user_gsg['money__sum'] is not None else 0  # 总邀请获得GSG数
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
        regex = re.compile(r'^(1|2|3|4)$')  # 1.今天 2.昨天 3.本月 4.上月
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
        month_first_day = str(start) + ' 00:00:00'  # 这个月的开始时间

        if int(type) == 1:  # 今天
            created_at_day = datetime.datetime.now().strftime('%Y-%m-%d')  # 当天日期
            start = str(created_at_day) + ' 00:00:00'  # 一天开始时间
            end = str(created_at_day) + ' 23:59:59'  # 一天结束时间
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(start) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        elif int(type) == 2:  # 昨天
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            start = str(yesterday) + ' 00:00:00'
            end = str(yesterday) + ' 23:59:59'
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(start) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        elif int(type) == 3:  # 当月
            end = datetime.date(year, month, day=monthCountDay).strftime('%Y-%m-%d')  # 获取当前月份最后一天
            start = str(start) + ' 00:00:00'
            end = str(end) + ' 23:59:59'
            sql = "select sum(pu.income), pu.club_id from promotion_userpresentation pu"
            sql += " where pu.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " and pu.user_id = '" + str(user.id) + "'"
            sql += " and pu.created_at >= '" + str(start) + "'"
            sql += " and pu.created_at <= '" + str(end) + "'"
            sql += " group by pu.club_id"
            monthly_summary = get_sql(sql)
        else:  # 上月
            this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
            end = this_month_start - timedelta(days=1)  # 上个月的最后一天
            start = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
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

        sql = "select club_id, sum(pu.bet_water) as sum_bet_water, sum(pu.dividend_water), " \
              "sum(pu.income) from promotion_userpresentation pu"
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
                income_dividend = reward_gradient_all(i["club_id"], monthly_summarys[i["club_id"]])
                all_income_dividend = to_decimal(coin_number_info[i["club_id"]][3])
                all_income_dividend = opposite_number(all_income_dividend)
                income_dividends = all_income_dividend * to_decimal(income_dividend)

                i["bet_water"] = normalize_fraction(coin_number_info[i["club_id"]][1], 8)
                i["dividend_water"] = normalize_fraction(coin_number_info[i["club_id"]][2], 8)
                i["income"] = normalize_fraction(coin_number_info[i["club_id"]][3], 8)
                income_dividends_s = normalize_fraction(income_dividends, 8)
                if income_dividends_s <= 0:
                    income_dividends_s = 0
                i["income_dividends"] = income_dividends_s
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
            all_bet_water = normalize_fraction(all_amount[0], 8)
        if all_amount[1] is None or all_amount[1] == 0:
            all_dividend_water = 0
        else:
            all_dividend_water = normalize_fraction(all_amount[1], 8)
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
            nowadays_bet_water = normalize_fraction(nowadays_amount[0], 8)
        if nowadays_amount[1] is None or nowadays_amount[1] == 0:
            nowadays_dividend_water = 0
        else:
            nowadays_dividend_water = normalize_fraction(nowadays_amount[1], 8)
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
            yesterday_bet_water = normalize_fraction(yesterday_amount[0], 8)
        if yesterday_amount[1] is None or yesterday_amount[1] == 0:
            yesterday_dividend_water = 0
        else:
            yesterday_dividend_water = normalize_fraction(yesterday_amount[1], 8)

        sql = "select DATE_FORMAT(pm.created_at,'%Y年%m月')months, pm.income, pm.income_dividend, pm.proportion " \
              "from promotion_presentationmonth pm"
        sql += " where pm.club_id = '" + str(club_id) + "'"
        sql += " and pm.user_id = '" + str(user.id) + "'"
        amount_list = get_sql(sql)
        month_list = []
        sum_coin = to_decimal(all_dividend_water)
        for i in amount_list:
            sum_coin += to_decimal(i[2])
            month_list.append({
                "months": i[0],
                "income": normalize_fraction(i[1], 8),
                "income_dividend": normalize_fraction(i[2], 8),
                "proportion": normalize_fraction(i[3], 8)
            })
        sum_coin = normalize_fraction(sum_coin,8)

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
        data = []

        sql = "select title from chat_clubrule"
        sql += " where is_deleted = 0"
        club_rule_info = get_sql(sql)
        for i in club_rule_info:
            if i[0] == "猜股指":
                number = 4
                a = 4
            elif i[0] == "篮球":
                number = 2
                a = 2
            elif i[0] == "足球":
                number = 3
                a = 1
            elif i[0] == "六合彩":
                number = 5
                a = 3
            elif i[0] == "龙虎斗":
                number = 6
                a = 6
            elif i[0] == "百家乐":
                number = 7
                a = 7
            elif i[0] == "股指PK":
                number = 8
                a = 5
            else:
                number = 9
                a = 8
            data.append({
                "name": i[0],
                "number": number,
                "a": a
            })
        data = sorted(data, key=lambda x: x["a"], reverse=False)
        return self.response({'code': 0, "data": data})


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
                start_time = str(
                    datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
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
        regex = re.compile(r'^(1|2|3|4|5|6|7|8)$')  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐 8.股指PK
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
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
        data_lists = []
        if len(user_id_list) != 0:
            sql_list = "p.bets, date_format( p.created_at, '%Y' ) as yearss,"
            sql_list += " date_format( p.created_at, '%Y-%m-%d' ) as years, " \
                        "date_format( p.created_at, '%H:%i:%s' ) as time,"
            sql_list += " date_format( p.created_at, '%Y%m%d%H%i%s' ) AS created_ats, " \
                        "p.status, p.source, u.nickname, u.avatar, p.user_id, p.id"
            sql = "select " + sql_list + " from promotion_promotionrecord p"
            sql += " inner join users_user u on p.user_id=u.id"
            sql += " where p.club_id = '" + club_id + "'"
            sql += " and p.created_at > '2018-09-07 00:00:00'"
            if len(user_id_list) > 0:
                sql += " and p.user_id in (" + ','.join(user_id_list) + ")"
            if int(type) == 2:  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐 8.股指PK
                sql += " and p.source = 2"
            elif int(type) == 3:
                sql += " and p.source = 1"
            elif int(type) == 4:
                sql += " and p.source = 4"
            elif int(type) == 5:
                sql += " and p.source = 3"
            elif int(type) == 6:
                sql += " and p.source = 7"
            elif int(type) == 7:
                sql += " and p.source = 6"
            elif int(type) == 8:
                sql += " and p.source = 5"
            sql += " and p.created_at >= '" + str(start_time) + "'"
            sql += " and p.created_at <= '" + str(end_time) + "'"
            sql += "group by p.id"
            sql += " order by created_ats desc"
            list_info = self.get_list_by_sql(sql)
            for i in list_info:
                if i[4] is not None:
                    if i[9] not in user_list:
                        user_list[i[9]] = i[9]
                    rule_name = ""
                    if int(i[6]) == 1:
                        rule_name = "足球"
                    if int(i[6]) == 2:
                        rule_name = "篮球"
                    if int(i[6]) == 3:
                        rule_name = "六合彩"
                    if int(i[6]) == 4:
                        rule_name = "猜股指"
                    if int(i[6]) == 5:
                        rule_name = "股指PK"
                    if int(i[6]) == 6:
                        rule_name = "百家乐"
                    if int(i[6]) == 7:
                        rule_name = "龙虎斗"
                    data_list.append({
                        "bets": normalize_fraction(i[0], 8),
                        "yearss": i[1],
                        "years": i[2],
                        "time": i[3],
                        "created_ats": i[4],
                        "status": i[5],
                        "rule": rule_name,
                        "nickname": i[7],
                        "avatar": i[8],
                        "user_id": i[9]
                    })

            list_infos = get_sql(sql)
            for i in list_infos:
                if i[4] is not None:
                    if i[9] not in user_list:
                        user_list[i[9]] = i[9]
                    data_lists.append({
                        "bets": normalize_fraction(i[0], 8),
                        "yearss": i[1],
                        "years": i[2],
                        "time": i[3],
                        "created_ats": i[4],
                        "status": i[5],
                        "rule": i[6],
                        "nickname": i[7],
                        "avatar": i[8]
                    })

        data_one_list = data_list
        data = []
        tmps = ''
        bet_water = 0

        for fav in data_lists:
            if int(fav["status"]) == 1:
                bet_water += to_decimal(fav["bets"])
        dividend_water = to_decimal(bet_water) * to_decimal(0.005)
        bet_water = str(normalize_fraction(bet_water, 8)) + " " + coin_name
        dividend_water = str(normalize_fraction(dividend_water, 8)) + " " + coin_name

        for fav in data_one_list:
            bets = to_decimal(0)
            if int(fav["status"]) == 0:
                status = "待结算"
                if self.request.GET.get('language') == 'en':
                    status = "Pending settlement"
            elif int(fav["status"]) == 2:
                status = "流盘"
                if self.request.GET.get('language') == 'en':
                    status = "Flow disk"
            else:
                status = "已结算"
                if self.request.GET.get('language') == 'en':
                    status = "Settled"
                bets = to_decimal(fav["bets"])
            divided_into = bets * to_decimal(0.005)
            divided_into = "+ " + str(normalize_fraction(divided_into, 8))

            pecific_dates = fav["years"]
            pecific_date = fav["time"]
            if tmps == pecific_dates:
                pecific_dates = ""
            else:
                tmps = pecific_dates
            data.append({
                "status": status,
                "divided_into": divided_into,
                "nickname": fav["nickname"],
                "avatar": fav["avatar"],
                "user_id": fav["user_id"],
                "bets": fav["bets"],
                "rule": fav["rule"],
                "pecific_dates": pecific_dates,
                "pecific_date": pecific_date,
            })

        return self.response({'code': 0,
                              "invite_number": len(user_list),
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
        club_id = self.request.GET.get('club_id')  # 俱乐部ID
        if int(club_id) == 1:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        sql = "select u.coin_accuracy, u.name from chat_club c"
        sql += " inner join users_coin u on c.coin_id=u.id"
        sql += " where c.id = '" + str(club_id) + "'"
        club_info = get_sql(sql)[0]
        coin_accuracy = club_info[0]  # 货币精度

        type = str(self.request.GET.get('type'))
        regex = re.compile(r'^(1|2|3|4|5|6|7|8)$')  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐 8.股票PK
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
                start_time = str(
                    datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
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
            else:
                # 默认开始时间
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
            else:
                # 默认日期 当天结束时间
                end_day = datetime.datetime.now().strftime('%Y-%m-%d')
                end_time = str(end_day) + ' 23:59:59'
                end_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month

        if start_year == end_year and start_month == end_month:
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            if current_year == 1:  # 获取上个月的年份
                last_month_year = current_year - 1
            else:
                last_month_year = current_year
            last_month_month = current_month - 1 or 12  # 获取上个月的月份

            if last_month_year == end_year and last_month_month == end_month:
                this_month_start = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)
                end = this_month_start - timedelta(days=1)  # 上个月的最后一天

                test_created_ats = datetime.datetime(end.year, end.month, 1).strftime('%Y%m')

                start = str(datetime.datetime(end.year, end.month, 1).strftime('%Y-%m-%d')) + ' 00:00:00'  # 上个月i第一天
                end = str(end.strftime('%Y-%m-%d')) + ' 23:59:59'
            else:
                start_year = datetime.datetime.now().year
                end_month = datetime.datetime.now().month

                test_created_ats = str(start_year) + str(end_month)

                weekDay, monthCountDay = calendar.monthrange(start_year, end_month)  # 当月第一天的星期 当月的总天数
                month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
                start = str(month_first_day) + ' 00:00:00'  # 本月第一天
                end = datetime.date(year=start_year, month=end_month, day=monthCountDay).strftime(
                    '%Y-%m-%d') + ' 23:59:59'  # 当月最后一天
        else:
            start_year = datetime.datetime.now().year
            end_month = datetime.datetime.now().month

            test_created_ats = str(start_year) + str(end_month)

            weekDay, monthCountDay = calendar.monthrange(start_year, end_month)  # 当月第一天的星期 当月的总天数
            month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
            start = str(month_first_day) + ' 00:00:00'  # 本月第一天
            end = datetime.date(year=start_year, month=end_month, day=monthCountDay).strftime(
                '%Y-%m-%d') + ' 23:59:59'  # 当月最后一天

        sql = "select date_format( pu.created_at, '%Y%m' ) AS created_ats, sum(pu.income) " \
              "from promotion_userpresentation pu"
        sql += " where pu.club_id = '" + str(club_id) + "'"
        sql += " and pu.user_id = '" + str(user.id) + "'"
        sql += " and pu.created_at >= '" + str(start) + "'"
        sql += " and pu.created_at <= '" + str(end) + "'"
        sql += " group by created_ats"
        the_month_list = get_sql(sql)
        month_list = {}
        if len(the_month_list) == 0:
            the_month_income_proportion = 0  # 本月兑换比例比例
            month_list[datetime.datetime.now().strftime('%Y%m')] = {
                "months": datetime.datetime.now().strftime('%Y%m'),
                "proportion": 0
            }
        else:
            the_month_list_sum = the_month_list[0][1]
            the_month_income_proportion = reward_gradient_all(club_id, the_month_list_sum)  # 本月兑换比例比例
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
            month_list[i[0]] = {
                "months": i[0],
                "proportion": normalize_fraction(i[1], 8)
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
        data = []
        if len(user_id_list) != 0:
            data_list = []
            data_lists = []
            sql_list = "p.bets, date_format( p.created_at, '%Y-%m-%d' ) as yearss,"
            sql_list += " date_format( p.created_at, '%H:%i:%s' ) as years,"
            sql_list += " p.source, u.nickname, u.avatar, sum(p.earn_coin),"
            sql_list += " date_format( p.created_at, '%Y%m' ) AS created_ats, p.user_id, " \
                        "date_format( p.created_at, '%Y%m%d%H%i%s' ) as times, p.id, p.status"

            sql = "select " + sql_list + " from promotion_promotionrecord p"
            sql += " inner join users_user u on p.user_id=u.id"
            sql += " where p.club_id = '" + club_id + "'"
            sql += " and p.created_at > '2018-09-07 00:00:00'"
            if len(user_id_list) > 0:
                sql += " and p.user_id in (" + ','.join(user_id_list) + ")"
            if int(type) == 2:  # 1.全部 2. 篮球  3.足球 4. 股票 5. 六合彩 6. 龙虎斗 7. 百家乐 8.股指PK
                sql += " and p.source = 2"
            elif int(type) == 3:
                sql += " and p.source = 1"
            elif int(type) == 4:
                sql += " and p.source = 4"
            elif int(type) == 5:
                sql += " and p.source = 3"
            elif int(type) == 6:
                sql += " and p.source = 7"
            elif int(type) == 7:
                sql += " and p.source = 6"
            elif int(type) == 8:
                sql += " and p.source = 5"
            sql += " and p.created_at >= '" + str(start_time) + "'"
            sql += " and p.created_at <= '" + str(end_time) + "'"
            sql += " and p.created_at > '2018-09-07 00:00:00'"
            sql += " and p.user_id in (" + ','.join(user_id_list) + ")"
            sql += "group by p.id"
            sql += " order by times desc"
            football_list = self.get_list_by_sql(sql)
            for i in football_list:
                rule_name = ""
                if int(i[3]) == 1:
                    rule_name = "足球"
                if int(i[3]) == 2:
                    rule_name = "篮球"
                if int(i[3]) == 3:
                    rule_name = "六合彩"
                if int(i[3]) == 4:
                    rule_name = "猜股指"
                if int(i[3]) == 5:
                    rule_name = "股指PK"
                if int(i[3]) == 6:
                    rule_name = "百家乐"
                if int(i[3]) == 7:
                    rule_name = "龙虎斗"
                if i[4] is not None:
                    if i[8] not in user_list:
                        user_list[i[8]] = i[8]
                    data_list.append({
                        "bets": to_decimal(i[0]),
                        "earn_coin": to_decimal(i[6]),
                        "yearss": i[1],
                        "years": i[2],
                        "rule": rule_name,
                        "nickname": i[4],
                        "avatar": i[5],
                        "user_id": i[8],
                        "created_ats": i[7],
                        "times": i[9],
                        "status": i[11]
                    })

            football_lists = get_sql(sql)
            for i in football_lists:
                if i[4] is not None:
                    if i[8] not in user_list:
                        user_list[i[8]] = i[8]
                    data_lists.append({
                        "bets": to_decimal(i[0]),
                        "earn_coin": to_decimal(i[6]),
                        "yearss": i[1],
                        "years": i[2],
                        "rule": i[3],
                        "nickname": i[4],
                        "avatar": i[5],
                        "created_ats": i[7],
                        "times": i[9]
                    })
            data_one_list = data_list

            sum_coin = 0
            for list in data_lists:
                if list["earn_coin"] > 0:
                    reward_coin = list["earn_coin"] - list["bets"]
                else:
                    reward_coin = list["earn_coin"]

                if list["created_ats"] == test_created_ats:
                    sum_coin += opposite_number(reward_coin)

            if test_created_ats not in month_list:
                test_proportion = 0
            else:
                test_proportion = month_list[test_created_ats]["proportion"]
            the_month_income_sum = to_decimal(sum_coin) * to_decimal(test_proportion)
            the_month_income_sum = normalize_fraction(the_month_income_sum, 8)
            if the_month_income_sum == 0:
                the_month_income_sum = 0

            tmps = ''
            for fav in data_one_list:
                if fav["created_ats"] in month_list:
                    proportion = to_decimal(month_list[fav["created_ats"]]["proportion"])
                else:
                    proportion = 0

                if fav["earn_coin"] > 0:
                    reward_coin = fav["earn_coin"] - fav["bets"]
                    result = 1
                else:
                    result = 0
                    reward_coin = fav["earn_coin"]

                dividend = normalize_fraction((opposite_number(reward_coin) * proportion), 8)
                if dividend == 0:
                    dividend = 0
                if dividend < 0 and dividend != 0:
                    dividend = -(dividend)
                    dividend = "-" + str(dividend)

                pecific_dates = fav["yearss"]
                pecific_date = fav["years"]
                if tmps == pecific_dates:
                    pecific_dates = ""
                else:
                    tmps = pecific_dates

                reward_coin = normalize_fraction(reward_coin, 8)
                if reward_coin < 0:
                    reward_coin = -(reward_coin)
                    reward_coin = "- " + str(reward_coin)
                data.append({
                    "nickname": fav["nickname"],
                    "avatar": fav["avatar"],
                    "user_id": fav["user_id"],
                    "bets": normalize_fraction(fav["bets"], 8),
                    "reward_coin": reward_coin,
                    "dividend": dividend,
                    "result": result,
                    "rule": fav["rule"],
                    "status": int(fav["status"]),
                    "pecific_dates": pecific_dates,
                    "pecific_date": pecific_date,
                })
        else:
            data = []
            the_month_income_sum = 0
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
            start_time = '2010-01-01 00:00:00'  # 开始时间

        if 'end_time' in self.request.GET:
            end_time = self.request.GET.get('end_time')
            end_time = str(end_time) + ' 23:59:59'
        else:
            enddays = datetime.datetime.now().strftime('%Y-%m-%d')
            end_time = str(enddays) + ' 23:59:59'  # 结束时间

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
                        "l.user_id=ui.invitee_one order by l.login_time desc limit 1) as login_time, ui.status"
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
            sql += " order by created_at desc"
            invitee_list = self.get_list_by_sql(sql)
            data = []
            for i in invitee_list:
                coin_info = ""
                if int(i[6]) == 2:
                    coin_info = "+ 20 GSG"
                user_list[i[0]] = i[0]
                if i[5] is None:
                    login_time = ""
                else:
                    login_time = i[5].strftime('%Y-%m-%d')
                data.append({
                    "user_id": i[0],
                    "avatar": i[1],
                    "nickname": i[2],
                    "created_at": i[3].strftime('%Y-%m-%d'),
                    "coin_info": coin_info,
                    "login_time": login_time
                })
        else:
            sql_list = "ui.invitee_one, u.avatar, u.nickname, u.created_at, ui.inviter_type,"
            sql_list += " (select l.login_time from users_loginrecord l where " \
                        "l.user_id=ui.invitee_one order by l.login_time desc limit 1) as login_time, ui.status"
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
                if int(i[6]) == 2:
                    coin_info = "+ 20 GSG"
                user_list[i[0]] = i[0]
                if i[5] is None:
                    login_time = ""
                else:
                    login_time = i[5].strftime('%Y-%m-%d')
                data.append({
                    "user_id": i[0],
                    "avatar": i[1],
                    "nickname": i[2],
                    "created_at": i[3].strftime('%Y-%m-%d'),
                    "coin_info": coin_info,
                    "login_time": login_time
                })
        user_number = len(user_list)
        return self.response({'code': 0, "user_number": user_number, "data": data})


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
        if user_infos[3] is None:
            login_time = ""
        else:
            login_time = user_infos[3].strftime('%Y-%m-%d')
        user_info = {
            "avatar": user_infos[0],
            "nickname": user_infos[1],
            "created_at": user_infos[2].strftime('%Y-%m-%d'),
            "login_time": login_time
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

        start_time = str(settings.PROMOTER_EXCHANGE_START_DATE) + ' 00:00:00'  # 活动开始时间
        enddays = datetime.datetime.now().strftime('%Y-%m-%d')
        end_time = str(enddays) + ' 23:59:59'  # 当前时间

        start_year = datetime.datetime.now().year
        end_month = datetime.datetime.now().month
        month_first_day = datetime.date(start_year, end_month, day=1).strftime('%Y-%m-%d')
        if int(end_month) - 1 == 0:
            before_month = 12
            before_yeas = int(start_year) - 1
            weekDay, monthCountDay = calendar.monthrange(before_yeas, before_month)
            before_first_day = datetime.date(before_yeas, before_month, day=monthCountDay).strftime('%Y-%m-%d')
            before_start = str(before_first_day) + ' 23:59:59'  # 本月第一天
        else:
            before_month = int(end_month) - 1
            before_yeas = int(start_year)
            weekDay, monthCountDay = calendar.monthrange(before_yeas, before_month)
            before_first_day = datetime.date(before_yeas, before_month, day=monthCountDay).strftime('%Y-%m-%d')
            before_start = str(before_first_day) + ' 23:59:59'  # 本月第一天
        start = str(month_first_day) + ' 00:00:00'  # 本月第一天

        data_list = {}
        if start != start_time:
            sql_list = "p.club_id, sum(p.bets), date_format( p.created_at, '%Y%m' ) AS created_ats, " \
                       "SUM((CASE WHEN p.earn_coin > 0 THEN p.earn_coin - p.bets ELSE p.earn_coin END)) AS earn_coin"

            sql = "select " + sql_list + " from promotion_promotionrecord p"
            sql += " inner join users_user u on p.user_id=u.id"
            sql += " where p.user_id = '" + str(invitee_id) + "'"
            sql += " and p.created_at >= '" + str(start_time) + "'"
            sql += " and p.status = 1"
            sql += " and p.created_at <= '" + str(before_start) + "'"
            sql += " and p.club_id in (" + ','.join(coin_id_list) + ")"
            sql += " group by p.club_id, created_ats"
            old_month_list = get_sql(sql)  # 往月
            for s in old_month_list:
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

        sql_list = "p.club_id, sum(p.bets), date_format( p.created_at, '%Y%m' ) AS created_ats, " \
                   "SUM((CASE WHEN p.earn_coin > 0 THEN p.earn_coin - p.bets ELSE p.earn_coin END)) AS earn_coin"

        sql = "select " + sql_list + " from promotion_promotionrecord p"
        sql += " inner join users_user u on p.user_id=u.id"
        sql += " where p.user_id = '" + str(invitee_id) + "'"
        sql += " and p.created_at >= '" + str(start) + "'"
        sql += " and p.status = '1' "
        sql += " and p.created_at <= '" + str(end_time) + "'"
        sql += " and p.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " group by p.club_id, created_ats"
        this_month_list = get_sql(sql)  # 本月
        for s in this_month_list:
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

        month_list = {}
        sql_list = "pm.club_id, date_format( pm.created_at, '%Y%m' ) AS created_ats, pm.proportion"
        sql = "select " + sql_list + " from promotion_presentationmonth pm"
        sql += " where pm.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " and pm.user_id = '" + str(user.id) + "'"
        sql += " and pm.created_at >= '" + str(start_time) + "'"
        sql += " and pm.created_at <= '" + str(end_time) + "'"
        amount_list = get_sql(sql)

        for i in amount_list:
            if i[0] not in month_list:
                month_list[i[0]] = {
                    i[1]: {
                        "months": i[1],
                        "proportion": i[2]
                    }
                }
            else:
                if i[1] in month_list[i[0]]:
                    month_list[i[0]][i[1]]["months"] = i[1]
                    month_list[i[0]][i[1]]["proportion"] = i[2]
                else:
                    month_list[i[0]] = {
                        i[1]: {
                            "months": i[1],
                            "proportion": i[2]
                        }
                    }

        sql_list = "pm.club_id, date_format( pm.created_at, '%Y%m' ) AS created_ats, sum(pm.income)"
        sql = "select " + sql_list + " from promotion_userpresentation pm"
        sql += " where pm.club_id in (" + ','.join(coin_id_list) + ")"
        sql += " and pm.user_id = '" + str(user.id) + "'"
        sql += " and pm.created_at >= '" + str(start) + "'"
        sql += " and pm.created_at <= '" + str(end_time) + "'"
        sql += " group by pm.club_id, created_ats"
        amount_list = get_sql(sql)

        for i in amount_list:
            if i[0] is not None:
                if i[0] not in month_list:
                    month_list[i[0]] = {
                        i[1]: {
                            "months": i[1],
                            "proportion": reward_gradient_all(i[0], i[2])
                        }
                    }
                else:
                    if i[1] in month_list[i[0]]:
                        month_list[i[0]][i[1]]["months"] = i[1]
                        month_list[i[0]][i[1]]["proportion"] = reward_gradient_all(i[0], i[2])
                    else:
                        month_list[i[0]] = {
                            i[1]: {
                                "months": i[1],
                                "proportion": reward_gradient_all(i[0], i[2])
                            }
                        }

        data = []
        for i in club_list:
            coin_accuracy = club_list[i]["coin_accuracy"]
            club_id = club_list[i]["club_id"]
            coin_name = club_list[i]["coin_name"]
            coin_icon = club_list[i]["coin_icon"]
            sum_bet = 0
            sum_bet_water = 0
            sum_income = 0
            sum_income_water = 0
            if club_id in data_list:
                for s in data_list[club_id]:
                    if club_id in month_list:
                        if s in month_list[club_id]:
                            income_dividend = month_list[club_id][s]["proportion"]
                        else:
                            income_dividend = 0
                    else:
                        income_dividend = 0
                    sum_bet += normalize_fraction(data_list[club_id][s]["bets"], 8)
                    income = normalize_fraction(data_list[club_id][s]["earn_coin"], 8)
                    sum_income += income
                    sum_income_water += to_decimal(income_dividend) * to_decimal(opposite_number(income))
                sum_bet_water = sum_bet * to_decimal(0.005)
            data.append({
                "coin_name": coin_name,
                "coin_icon": coin_icon,
                "sum_bet": sum_bet,
                "sum_bet_water": normalize_fraction(sum_bet_water, 8),
                "sum_income": sum_income,
                "sum_income_water": normalize_fraction(sum_income_water, 8)
            })
        return self.response({'code': 0, "user_info": user_info, "data": data})
