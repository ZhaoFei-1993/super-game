# -*- coding: UTF-8 -*-
from base.app import ListAPIView, ListCreateAPIView
from django.db import connection
from base.function import LoginRequired
from .serializers import ClubListSerialize, ClubRuleSerialize, ClubBannerSerialize, RecordSerialize
from chat.models import Club, ClubRule, ClubBanner, ClubIdentity, ClubIncome
from base import code as error_code
from base.exceptions import ParamErrorException
from users.models import DailyLog, Coin, RecordMark, UserRecharge, UserPresentation, UserCoin
from django.db.models import Q
from utils.functions import message_hints, normalize_fraction, get_sql, to_decimal
from django.db.models import Sum
import datetime
import re
import calendar
from datetime import timedelta
from django.conf import settings
from utils.cache import get_cache, set_cache, delete_cache
from promotion.models import PromotionRecord
from promotion.models import UserPresentation as Promotion, UserPresentation as PromotionUserPresentation
from quiz.models import Record as QuizRecord, Rule as QuizRule
from guess.models import Record as GuessRecord, RecordStockPk as GuesspkRecord, StockPk, Play, Stock
from marksix.models import SixRecord, Option


class ClublistView(ListAPIView):
    """
    俱乐部列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = ClubListSerialize

    def get_queryset(self):
        if 'name' in self.request.GET:
            name = self.request.GET.get('name')

            if self.request.GET.get('language') == 'en':
                chat_list = Club.objects.filter(room_title_en__icontains=name).order_by('user', '-is_recommend')
            else:
                chat_list = Club.objects.filter(room_title__icontains=name).order_by('user', '-is_recommend')
        else:
            chat_list = Club.objects.filter(is_dissolve=0).order_by('user', '-is_recommend')
        return chat_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user = request.user

        # 发消息
        # UserMessage.objects.add_system_user_message(user=user)

        is_sign = DailyLog.objects.is_signed(user.id)  # 是否签到
        is_message = message_hints(user.id)  # 是否有未读消息
        if user.is_block == 1:
            raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)

        # 获取俱乐部货币、在线人数
        coins = Coin.objects.get_coins_map_id()

        data = []
        for item in items:
            club_id = item['id']
            # is_identity = ClubIdentity.objects.filter(is_deleted=0, user_id=int(user.id), club_id=club_id).count()
            coin = coins[item['coin_id']]
            user_number = Club.objects.get_club_online(club_id)

            data.append(
                {
                    "club_id": club_id,
                    "room_title": item['title'],
                    "autograph": item['club_autograph'],
                    "user_number": user_number,
                    "room_number": item['room_number'],
                    "coin_name": coin.name,
                    "coin_key": coin.id,
                    "icon": item['icon'],
                    "coin_icon": coin.icon,
                    # "is_identity": is_identity,
                    "is_recommend": item['is_recommend']
                }
            )

        content = {
            "code": 0,
            "data": data,
            "is_sign": is_sign,
            "is_message": is_message,
            "name": user.nickname,
            "avatar": user.avatar
        }
        return self.response(content)


class ClubRuleView(ListAPIView):
    """
    玩法列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = ClubRuleSerialize

    def get_queryset(self):
        chat_rule_list = ClubRule.objects.filter(is_deleted=0).order_by('sort')
        return chat_rule_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        user_id = self.request.user.id
        items = results.data.get('results')
        is_number = RecordMark.objects.filter(user_id=int(user_id)).count()
        if is_number == 0:
            record_mark_info = RecordMark.objects.insert_record_mark(user_id)
        else:
            record_mark_info = RecordMark.objects.get(user_id=user_id)
        data = []
        for item in items:
            if int(item['id']) == 1:
                is_mark = record_mark_info.quiz_football
            elif int(item['id']) == 7:
                is_mark = record_mark_info.quiz_basketball
            elif int(item['id']) == 2:
                is_mark = record_mark_info.six
            elif int(item['id']) == 3:
                is_mark = record_mark_info.guess
            elif int(item['id']) == 4:
                is_mark = record_mark_info.dragon_tiger
            elif int(item['id']) == 5:
                is_mark = record_mark_info.baccarat
            else:
                is_mark = record_mark_info.guess_pk
            if int(item['id']) == 5:
                data.append(
                    {
                        "clubrule_id": item['id'],
                        "name": item['name'],
                        "icon": item['icon'],
                        "room_number": item['number'],
                        "table_id": 1,
                        "is_mark": is_mark
                    }
                )
            else:
                data.append(
                    {
                        "clubrule_id": item['id'],
                        "name": item['name'],
                        "icon": item['icon'],
                        "room_number": item['number'],
                        "is_mark": is_mark
                    }
                )
        return self.response({"code": 0, "data": data})


class BannerView(ListAPIView):
    """
    俱乐部轮播图
    """
    permission_classes = (LoginRequired,)
    serializer_class = ClubBannerSerialize

    def get_queryset(self):
        if self.request.GET.get('language') == 'en':
            query = ClubBanner.objects.filter(is_delete=0, language='en')
        else:
            query = ClubBanner.objects.filter(~Q(language='en'), is_delete=0)
        return query

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "img_url": item['image'],
                    "action": item['active'],
                    "type": item['banner_type'],
                    "param": item['param'],
                    "title": item['title'],
                }
            )
        return self.response({"code": 0, "data": data})


class MarkClubView(ListAPIView):
    """
    玩法记录下俱乐部
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user_id = str(self.request.user.id)
        rule_id = self.request.GET.get("rule_id")
        data = []

        if int(rule_id) == 1 or int(rule_id) == 7:  # 1.足球, 2.六合彩, 3.猜股票, 4.龙虎斗, 5.百家乐, 6.股票PK, 7.篮球
            parent_id_map = {1: 2, 7: 1}
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from quiz_record r"
            sql += " inner join chat_club cc on r.roomquiz_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " inner join quiz_quiz on r.quiz_id=quiz_quiz.id"
            sql += " inner join quiz_category cate on cate.id=quiz_quiz.category_id"
            sql += " where r.user_id = '" + str(user_id) + "'" + ' and '
            sql += "cate.parent_id={parent_id}".format(parent_id=parent_id_map[int(rule_id)])
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        elif int(rule_id) == 2:
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from marksix_sixrecord r"
            sql += " inner join chat_club cc on r.club_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " where r.user_id = '" + str(user_id) + "'"
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        elif int(rule_id) == 3:
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from guess_record r"
            sql += " inner join chat_club cc on r.club_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " where r.user_id = '" + str(user_id) + "'"
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        elif int(rule_id) == 4:
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from dragon_tiger_dragontigerrecord r"
            sql += " inner join chat_club cc on r.club_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " where r.user_id = '" + str(user_id) + "'"
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        elif int(rule_id) == 5:
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from banker_bankerbigheadrecord r"
            sql += " inner join chat_club cc on r.club_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " where r.user_id = '" + str(user_id) + "'"
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        else:
            sql_list = " cc.id, c.icon, count(cc.id) as number"

            sql = "select " + sql_list + " from guess_recordstockpk r"
            sql += " inner join chat_club cc on r.club_id=cc.id"
            sql += " inner join users_coin c on cc.coin_id=c.id"
            sql += " where r.user_id = '" + str(user_id) + "'"
            sql += " group by cc.id, c.icon"
            sql += " order by number desc"
        print(sql)
        list = self.get_list_by_sql(sql)
        for i in list:
            data.append({
                "club_id": i[0],
                "coin_icon": i[1]
            })
        return self.response({"code": 0, "data": data})


class ClubMonthView(ListAPIView):
    """
    月份
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        data = []
        list = {}
        key = "CLUB_DATA_MONTH_INFO"
        year = datetime.date.today().year  # 获取当前年份
        month = datetime.date.today().month  # 获取当前月份
        this_month = datetime.date(year, month, day=1)  # 当月
        this_months = str(this_month.month) + "月"

        last_month = this_month - timedelta(days=1)  # 上月
        last_months = str(last_month.month) + "月"

        lasts_month = last_month - timedelta(days=32)  # 上上月
        lasts_months = str(lasts_month.month) + "月"

        lasts_year = lasts_month.year
        lasts_monthss = lasts_month.month
        weekDay, monthCountDay = calendar.monthrange(lasts_year, lasts_monthss)  # 获取当月第一天的星期和当月的总天数
        lasts_start = str(datetime.date(lasts_year, lasts_monthss, day=1).strftime('%Y-%m-%d')) + " 00:00:00"  # 获取当月第一天
        lasts_end = str(
            datetime.date(lasts_year, lasts_monthss, day=monthCountDay).strftime(
                '%Y-%m-%d')) + " 23:59:59"  # 获取当前月份最后一天
        data.append({
            "month_id": 3,
            "month": lasts_months
        })
        list[3] = {
            "month_id": 3,
            "month": lasts_months,
            "start": lasts_start,
            "end": lasts_end
        }

        last_year = last_month.year
        last_monthss = last_month.month
        weekDay, monthCountDay = calendar.monthrange(last_year, last_monthss)  # 获取当月第一天的星期和当月的总天数
        last_start = str(datetime.date(last_year, last_monthss, day=1).strftime('%Y-%m-%d')) + " 00:00:00"  # 获取当月第一天
        last_end = str(
            datetime.date(last_year, last_monthss, day=monthCountDay).strftime('%Y-%m-%d')) + " 23:59:59"  # 获取当前月份最后一天
        data.append({
            "month_id": 2,
            "month": last_months
        })
        list[2] = {
            "month_id": 2,
            "month": last_months,
            "start": last_start,
            "end": last_end
        }

        this_year = this_month.year
        this_monthss = this_month.month
        weekDay, monthCountDay = calendar.monthrange(this_year, this_monthss)  # 获取当月第一天的星期和当月的总天数
        start = str(datetime.date(this_year, this_monthss, day=1).strftime('%Y-%m-%d')) + " 00:00:00"  # 获取当月第一天
        end = str(
            datetime.date(this_year, this_monthss, day=monthCountDay).strftime('%Y-%m-%d')) + " 23:59:59"  # 获取当前月份最后一天
        data.append({
            "month_id": 1,
            "month": this_months
        })
        list[1] = {
            "month_id": 1,
            "month": this_months,
            "start": start,
            "end": end
        }
        set_cache(key, list)
        return self.response({"code": 0, "data": data})


class ClubUserView(ListAPIView):
    """
    用户列表
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        data = []
        type = int(request.GET.get("type"))
        if 'type' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        coin_id = int(Club.objects.get_one(pk=club_id).coin_id)
        print(coin_id)
        user_list = str(settings.TEST_USER_IDS)

        sql_list = " u.id, u.area_code, u.telephone, u.is_block, date_format( u.created_at, '%Y-%m-%d' ) as time,"
        if type == 1: # 登陆
            sql_list += " max(l.login_time) as sb_time"
        else:    # 激活
            sql_list += " max(ur.created_at) as sb_time"
        sql = "select " + sql_list + " from users_userrecharge ur"
        sql += " inner join users_user u on ur.user_id=u.id"
        sql += " inner join users_loginrecord l on l.user_id=u.id"
        sql += " where u.is_robot = 0"
        sql += " and u.id not in " + user_list
        sql += " and ur.coin_id = '" + str(coin_id) + "'"
        if "telephone" in request.GET:
            telephone = "%" + str(request.GET.get("telephone")) + "%"
            sql += " and u.telephone like '" + telephone + "'"
        sql += " group by u.id"
        if type == 1:  # 登陆
            sql += " order by sb_time desc"
        else:  # 激活
            sql += " order by u.created_at desc"
        list = self.get_list_by_sql(sql)
        for i in list:
            if i[5] is None:
                sb_time = ""
            else:
                sb_time = i[5].strftime('%Y-%m-%d')
            telephone = str(i[2])
            telephone = str(telephone[0:3]) + "***" + str(telephone[7:])
            data.append({
                "user_id": i[0],
                "area_code": i[1],
                "telephone": telephone,
                "is_block": i[3],
                "time": i[4],
                "sb_time": sb_time
            })

        return self.response({"code": 0, "data": data})


class ClubHomeView(ListAPIView):
    """
    首页
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        day = datetime.datetime.now().strftime('%Y-%m-%d')
        day_start = str(day) + " 00:00:00"
        day_end = str(day) + " 23:59:59"
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_start = str(yesterday) + ' 00:00:00'
        yesterday_end = str(yesterday) + ' 23:59:59'


        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)
        icon = coin_info.icon
        user_list = settings.TEST_USER_ID
        print("user_list=====================", user_list)
        user_number = UserRecharge.objects.filter(~Q(user_id__in=user_list),
                                                  coin_id=int(coin_info.id)
                                                  ).values('user_id').distinct().count()    # 总用户
        user_day_number = UserRecharge.objects.filter(~Q(user_id__in=user_list),
                                                      coin_id=int(coin_info.id), created_at__gte=day_start,
                                                      created_at__lte=day_end).values('user_id').distinct().count()    # 今天新增加
        user_two_number = UserRecharge.objects.filter(~Q(user_id__in=user_list),
                                                      coin_id=int(coin_info.id),
                                                      created_at__gte=yesterday_start,
                                                      created_at__lte=yesterday_end
                                                      ).values('user_id').distinct().count()    # 昨天新增加

        recharge_coin = UserRecharge.objects.filter(~Q(user_id__in=user_list),
                                                    coin_id=int(coin_info.id)).aggregate(Sum('amount'))
        if recharge_coin['amount__sum'] is None:
            sum_recharge = 0
        else:
            sum_recharge = normalize_fraction(recharge_coin['amount__sum'], coin_accuracy)       # 总充值

        presentat_coin = UserPresentation.objects.filter(~Q(user_id__in=user_list),
                                                         coin_id=int(coin_info.id), status=1).aggregate(Sum('amount'))
        if presentat_coin['amount__sum'] is None:
            sum_presentat = 0
        else:
            sum_presentat = normalize_fraction(presentat_coin['amount__sum'], coin_accuracy)       # 总提现

        user_coin = UserCoin.objects.filter(~Q(user_id__in=user_list),
                                            coin_id=int(coin_info.id), user__is_block=0,
                                            user__is_robot=0).aggregate(Sum('balance'))
        if user_coin['balance__sum'] is None:
            sum_coin = 0
        else:
            sum_coin = normalize_fraction(user_coin['balance__sum'], coin_accuracy)       # 总金额

        sum_list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                  club_id=int(club_id),
                                                  user__is_block=0).aggregate(Sum('bets'))
        if sum_list['bets__sum'] is None:
            sum_bet_water = 0
        else:
            sum_bet_water = normalize_fraction(sum_list['bets__sum'], coin_accuracy)       # 总投注流水

        sum_bets = ClubIncome.objects.filter(club_id=int(club_id)).aggregate(Sum('earn_coin'))
        sum_dividend_water = PromotionUserPresentation.objects.filter(club_id=int(club_id),
                                                                      created_at__gte='2018-12-03 00:00:00'
                                                                      ).aggregate(Sum('dividend_water'))
        if sum_dividend_water['dividend_water__sum'] is None:
            sum_dividend_water = 0
        else:
            sum_dividend_water = normalize_fraction(sum_dividend_water['dividend_water__sum'], coin_accuracy)
        if sum_bets['earn_coin__sum'] is None:
            sum_bets = 0
        else:
            sum_bets = normalize_fraction((sum_bets['earn_coin__sum'] - sum_dividend_water), coin_accuracy)  # 总盈亏

        sum_bets = normalize_fraction(sum_bets, coin_accuracy)
        data = {
            "sum_earn_coin": sum_bet_water,    # 总投注流水
            "sum_bets": sum_bets,    # 总盈亏
            "sum_coin": sum_coin,    # 总金额
            "coin_name": coin_info.name,    # 货币昵称
            "icon": icon,    # 货币头像
            "user_number": user_number,    # 总用户
            "user_day_number": user_day_number,   # 今天新增加
            "user_two_number": user_two_number,   # 昨天新增加
            "sum_recharge": sum_recharge,       # 总充值
            "sum_presentat": sum_presentat,    # 总提现
        }
        return self.response({"code": 0, "data": data})


class ClubUserInfoView(ListAPIView):
    """
    用户详情
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        club_info = Club.objects.get_one(pk=club_id)

        coin_id = int(club_info.coin_id)
        coin_info = Coin.objects.get_one(pk=coin_id)
        coin_accuracy = coin_info.coin_accuracy
        icon = coin_info.name

        user_id = int(request.GET.get("user_id"))
        user_coin = UserCoin.objects.get(user_id=user_id, coin_id=coin_id)
        balance = normalize_fraction(user_coin.balance, coin_accuracy)
        telephone = str(user_coin.user.telephone)
        telephone = str(telephone[0:3]) + "***" + str(telephone[7:])
        data = {
            "user_id": user_id,
            "telephone": telephone,
            "avatar": user_coin.user.avatar,
            "area_code": user_coin.user.area_code,
            "balance": balance,
            "coin_id": coin_id,
            "name": icon
        }
        return self.response({"code": 0, "data": data})


class ClubBetListView(ListAPIView):
    """
    俱乐部投注列表
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        month_id = int(self.request.GET.get("month_id"))
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)

        key = "CLUB_DATA_MONTH_INFO"
        month_info = get_cache(key)
        month_info = month_info[month_id]
        month_month = month_info["month"]
        month_start = month_info["start"]
        month_end = month_info["end"]

        user_list = str(settings.TEST_USER_IDS)
        club_rule = str(settings.CLUB_RULE)
        user_lists = settings.TEST_USER_ID

        key = "MONTH_BET_LIST_" + str(club_id) + "_" + str(month_month) + str(type)
        delete_cache(key)
        list = get_cache(key)
        if list is None:
            sql_list = "date_format( p.created_at, '%Y年%m月%d日' ) as years, sum(p.bets), "
            sql_list += "sum(p.earn_coin), "
            sql_list += "date_format( p.created_at, '%Y%m%d' ) as time, date_format( p.created_at, '%Y-%m-%d' ) as sb"
            sql = "select " + sql_list + " from chat_clubincome p"
            sql += " where p.club_id = '" + str(club_id) + "'"
            sql += " and p.source in " + club_rule
            sql += " and p.created_at >= '" + str(month_start) + "'"
            sql += " and p.created_at <= '" + str(month_end) + "'"
            sql += "group by years, sb, time"
            sql += " order by time desc"
            print("sql===================", sql)
            list_info = get_sql(sql)
            list = []
            for i in list_info:
                if i[2] is None:
                    earn_coin = 0
                else:
                    earn_coin = i[2]
                print("收益=============", earn_coin)
                test_time = i[4] + ' 00:00:00'
                test_times = i[4] + ' 23:59:59'
                divided_into = Promotion.objects.filter(~Q(user_id__in=user_lists),
                                                        club_id=int(club_id),
                                                        created_at__gte=test_time,
                                                        created_at__lte=test_times).aggregate(Sum('dividend_water'))
                if divided_into['dividend_water__sum'] is None:
                    divided_into = 0
                else:
                    divided_into = normalize_fraction(divided_into['dividend_water__sum'], coin_accuracy)  # 当天流水分成
                list.append({
                    "time": i[0],
                    "sb_time": i[4],
                    "bets": normalize_fraction(i[1], coin_accuracy),
                    "divided_into": divided_into,
                    "earn_coin": normalize_fraction(earn_coin, coin_accuracy)
                })
            if month_id in [2, 3]:
                set_cache(key, list)
        return self.response({"code": 0, "list": list})


class ClubBetsView(ListAPIView):
    """
    盈利奖励
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)

        user_list = str(settings.TEST_USER_IDS)

        sql_list = "date_format( p.created_at, '%Y年%m月' ) as years, "
        sql_list += "sum(p.earn_coin) as profit, "
        sql_list += "date_format( p.created_at, '%Y%m' ) as time"
        sql = "select " + sql_list + " from chat_clubincome p"
        sql += " where p.club_id = '" + str(club_id) + "'"
        sql += " group by years, time"
        sql += " order by time desc"
        print("sql==========", sql)
        list_info = get_sql(sql)
        list = []
        for i in list_info:
            if i[1] is None:
                earn_coin = 0
            else:
                earn_coin = i[1]
            list.append({
                "time": i[0],
                "earn_coin": normalize_fraction(earn_coin, coin_accuracy)
            })
        return self.response({"code": 0, "list": list})


class ClubRewardView(ListAPIView):
    """
    奖励列表
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user_id = self.request.GET.get('user_id')
        if 'user_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        type = self.request.GET.get("type")
        regex = re.compile(r'^(1|2)$')  # 1 流水  2 分成
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)

        list = []
        sql_list = "date_format( p.created_at, '%Y-%m-%d %H:%i:%s' ) as years, "
        if int(type) == 1:
            sql_list += "p.dividend_water, "
        else:
            sql_list += "p.income_dividend, "
        sql_list += "date_format( p.created_at, '%Y%m%d%H%i%s' ) as time"
        if int(type) == 1:
            sql = "select " + sql_list + " from promotion_userpresentation p"
        else:
            sql = "select " + sql_list + " from promotion_presentationmonth p"

        sql += " where p.club_id = '" + str(club_id) + "'"
        sql += " and p.user_id = '" + str(user_id) + "'"
        sql += " order by time desc"
        list_info = self.get_list_by_sql(sql)

        if int(type) == 1:
            sql_list = "sum(p.dividend_water)"
        else:
            sql_list = "sum(p.income_dividend)"
        if int(type) == 1:
            sql = "select " + sql_list + " from promotion_userpresentation p"
        else:
            sql = "select " + sql_list + " from promotion_presentationmonth p"

        sql += " where p.club_id = '" + str(club_id) + "'"
        sql += " and p.user_id = '" + str(user_id) + "'"
        lists = get_sql(sql)
        sum_earn_coin = 0
        for i in lists:
            if i[0] is not None:
                sum_earn_coin = normalize_fraction(i[0], coin_accuracy)

        for i in list_info:
            if int(type) == 1:
                types = "流水奖励"
            else:
                types = "分成奖励"
            list.append({
                "time": i[0],
                "type": types,
                "earn_coin": normalize_fraction(i[1], coin_accuracy)
            })
        return self.response({"code": 0, "list": list, "sum_earn_coin": sum_earn_coin})


class PayClubView(ListAPIView):
    """
    俱乐部充值提现明细
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        month_id = int(self.request.GET.get("month_id"))
        if "type" in request.GET:
            type = int(self.request.GET.get("type"))   # 1.充值 2.提现
        else:
            type = 1
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)
        name = coin_info.name
        key = "CLUB_DATA_MONTH_INFO"
        month_info = get_cache(key)
        month_info = month_info[month_id]
        month_start = month_info["start"]
        month_month = month_info["month"]
        month_end = month_info["end"]

        # cache_file = settings.CACHE_DIR + '/' + str(club_id) + '/' + str(quiz_id) + '/' + self.KEY_CLUB_QUIZ_BET_USERS
        user_list = settings.TEST_USER_ID

        user_recharge = UserRecharge.objects.filter(~Q(user_id__in=user_list), coin_id=int(coin_info.id),
                                                    created_at__gte=month_start,
                                                    created_at__lte=month_end).aggregate(Sum('amount'))
        if user_recharge['amount__sum'] is None:
            sum_recharge = 0
        else:
            sum_recharge = normalize_fraction(user_recharge['amount__sum'], coin_accuracy)       # 当月总充值

        if type == 1:   # 1.充值 2.提现
            recharge_user_number = UserRecharge.objects.filter(~Q(user_id__in=user_list), coin_id=int(coin_info.id),
                                                               created_at__gte=month_start,
                                                               created_at__lte=month_end).values('user_id').distinct().count()  # 当月总充值人数
        else:
            recharge_user_number = UserPresentation.objects.filter(~Q(user_id__in=user_list),
                                                                   coin_id=int(coin_info.id),
                                                                   created_at__gte=month_start,
                                                                   created_at__lte=month_end).values('user_id').distinct().count()

        user_presentat = UserPresentation.objects.filter(~Q(user_id__in=user_list),
                                                         coin_id=int(coin_info.id), status=1,
                                                         created_at__gte=month_start,
                                                         created_at__lte=month_end).aggregate(Sum('amount'))
        if user_presentat['amount__sum'] is None:
            sum_presentat = 0
        else:
            sum_presentat = normalize_fraction(user_presentat['amount__sum'], coin_accuracy)  # 当月总提现

        key = "MONTH_RECHARGE_" + str(club_id) + "_" + str(month_month) + str(type)
        delete_cache(key)
        list = get_cache(key)
        if list is None:
            if type == 1:     # 1.充值 2.提现
                list_info = UserRecharge.objects.filter(~Q(user_id__in=user_list),
                                                        coin_id=int(coin_info.id),
                                                        created_at__gte=month_start,
                                                        created_at__lte=month_end).order_by("-created_at")
            else:
                list_info = UserPresentation.objects.filter(~Q(user_id__in=user_list),
                                                            coin_id=int(coin_info.id),
                                                            created_at__gte=month_start,
                                                            created_at__lte=month_end).order_by("-created_at")
            list = []
            for i in list_info:
                telephone = str(i.user.telephone)
                user_number = "+" + str(i.user.area_code) + " " + str(telephone[0:3]) + "***" + str(telephone[7:])
                list.append({
                    "user_id": i.user_id,
                    "amount": normalize_fraction(i.amount, coin_accuracy),
                    "telephone": user_number,
                    "created_at": i.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            if month_id in [2, 3]:
                set_cache(key, list)

        if "page_size" in request.GET:
            page_size = int(self.request.GET.get("page_size"))
        else:
            page_size = 10

        if "page" in request.GET:
            page = int(self.request.GET.get("page"))  # 1.充值 2.提现
            if page == 0:
                page = 1
        else:
            page = 1
        head = (page - 1) * page_size
        if page == 1:
            head = 0

        tail = page * page_size
        data = {
            "sum_recharge": sum_recharge,   # 总充值
            "name": name,
            "recharge_user_number": recharge_user_number,   # 总充值人数
            "sum_presentat": sum_presentat,   # 总提现
            "list": list[head:tail],   # 数据详情
        }

        return self.response({"code": 0, "data": data})


class ClubDayBetView(ListCreateAPIView):
    """
    单天投注记录
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        sb_time = str(self.request.GET.get("sb_time"))
        start = sb_time + " 00:00:00"
        end = sb_time + " 23:59:59"

        type = int(self.request.GET.get("type"))   # 1.1足球  2.7篮球 3. 2六合彩 4. 3股票 5. 6股票PK 6. 5百家乐 7.4龙虎斗
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
        elif int(type) == 5:
            type = 6
        elif int(type) == 6:
            type = 5
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)

        user_list = settings.TEST_USER_ID

        if type == 0:
            number = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                    club_id=int(club_id), created_at__gte=start,
                                                    created_at__lte=end, user__is_block=0
                                                    ).values('user_id').distinct().count()
            sum_bets = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                      club_id=int(club_id), created_at__gte=start,
                                                      created_at__lte=end, user__is_block=0).aggregate(Sum('bets'))
            sum_earn_coin = ClubIncome.objects.filter(club_id=int(club_id),
                                                      created_at__gte=start,
                                                      created_at__lte=end).aggregate(Sum('earn_coin'))

        else:
            number = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                    club_id=int(club_id), created_at__gte=start, source=type,
                                                    created_at__lte=end, user__is_block=0
                                                    ).values('user_id').distinct().count()
            sum_bets = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                      club_id=int(club_id), created_at__gte=start, source=type,
                                                      created_at__lte=end, user__is_block=0).aggregate(Sum('bets'))
            sum_earn_coin = ClubIncome.objects.filter(club_id=int(club_id),
                                                      created_at__gte=start,
                                                      created_at__lte=end,
                                                      source=type).aggregate(Sum('earn_coin'))

        if sum_bets['bets__sum'] is None:
            sum_bets = 0
        else:
            sum_bets = normalize_fraction(sum_bets['bets__sum'], coin_accuracy)  # 总投注流水

        if sum_earn_coin['earn_coin__sum'] is None:
            sum_earn_coin = 0
        else:
            sum_earn_coin = normalize_fraction(sum_earn_coin['earn_coin__sum'], coin_accuracy)  # 总盈亏

        return self.response({"code": 0,
                              "number": number,
                              "sum_bets": sum_bets,
                              "sum_earn_coin": sum_earn_coin,
                              "coin_name": coin_info.name})


class ClubRecordView(ListAPIView):
    """
    下注记录
    """
    permission_classes = (LoginRequired,)
    serializer_class = RecordSerialize

    def get_queryset(self):
        type = int(self.request.GET.get('type'))   # 0,全部 剩下分类按照玩法列表
        if 'type' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        user = self.request.user
        club_id = int(self.request.GET.get("club_id"))
        if 'club_id' not in self.request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        key = "CLUB_INCOME_ALL"
        key_user_id = get_cache(key)
        if (key_user_id is not None) and int(user.id) == int(key_user_id) or user.id == 1490:
            pass
        else:
            club_identity = ClubIdentity.objects.filter(is_deleted=0, club_id=club_id, user_id=int(user.id)).count()
            if club_identity != 1:
                raise ParamErrorException(error_code.API_110114_BACKEND_BANKER)
        user_list = settings.TEST_USER_ID
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
        elif int(type) == 5:
            type = 6
        elif int(type) == 6:
            type = 5
        if type == 0:
            if 'sb_time' in self.request.GET:
                sb_time = str(self.request.GET.get("sb_time"))
                start = sb_time + " 00:00:00"
                end = sb_time + " 23:59:59"
                if 'user_id' in self.request.GET:
                    user_id = self.request.GET.get('user_id')
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          user_id=user_id,
                                                          club_id=club_id,
                                                          open_prize_time__range=[start, end],
                                                          user__is_block=0).order_by('-open_prize_time')
                else:
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          club_id=club_id,
                                                          open_prize_time__range=[start, end],
                                                          user__is_block=0).order_by('-open_prize_time')
            else:
                if 'user_id' in self.request.GET:
                    user_id = self.request.GET.get('user_id')
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          user_id=user_id,
                                                          club_id=club_id,
                                                          user__is_block=0).order_by('-open_prize_time')
                else:
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          club_id=club_id,
                                                          user__is_block=0).order_by('-open_prize_time')
        else:
            if 'sb_time' in self.request.GET:
                sb_time = str(self.request.GET.get("sb_time"))
                start = sb_time + " 00:00:00"
                end = sb_time + " 23:59:59"
                if 'user_id' in self.request.GET:
                    user_id = self.request.GET.get('user_id')
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          user_id=user_id,
                                                          source=type,
                                                          club_id=club_id,
                                                          open_prize_time__range=[start, end],
                                                          user__is_block=0).order_by('-open_prize_time')
                else:
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          source=type,
                                                          club_id=club_id,
                                                          open_prize_time__range=[start, end],
                                                          user__is_block=0).order_by('-open_prize_time')
            else:
                if 'user_id' in self.request.GET:
                    user_id = self.request.GET.get('user_id')
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          user_id=user_id,
                                                          source=type,
                                                          club_id=club_id,
                                                          user__is_block=0).order_by('-open_prize_time')
                else:
                    list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                          ~Q(status=0),
                                                          source=type,
                                                          club_id=club_id,
                                                          user__is_block=0).order_by('-open_prize_time')
        return list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            type = int(item['source'])
            record_id = int(item['record_id'])
            list = ''
            if type in (1, 2):
                quiz_info = QuizRecord.objects.get(id=record_id)
                odds = str(quiz_info.odds)
                rule = str(QuizRule.TYPE_CHOICE[int(quiz_info.rule.type)][1])
                option = str(quiz_info.option.option.option)
                options = rule + ": " + option + "/" + odds
                name = str(quiz_info.quiz.host_team) + " VS " + str(quiz_info.quiz.guest_team)
                list = {
                    "titlev": name,
                    "bets": normalize_fraction(item['bets'], int(item['coin_info'].coin_accuracy)),
                    "options": options
                }
            elif type == 3:
                record_info = SixRecord.objects.get(id=record_id)
                issue = record_info.issue
                bet_coin = record_info.bet_coin
                number = to_decimal(record_info.bet)

                play = record_info.play
                option_id = record_info.option_id
                res = record_info.content
                language = self.request.GET.get('language')
                res_list = res.split(',')
                if (play.id != 1 and not option_id) or play.id == 8:  # 排除连码和特码
                    content_list = []
                    for pk in res_list:
                        if language == 'zh':
                            title = Option.objects.get(id=pk).option
                        else:
                            title = Option.objects.get(id=pk).option_en
                        content_list.append(title)
                    res = ','.join(content_list)

                # 判断注数
                if language == 'zh':
                    last = '注'
                else:
                    last = 'notes'
                title = ''
                if option_id:
                    title = Option.objects.get(id=option_id).option

                if play.id == 8:
                    next = '共' + str(record_info.bet) + last
                    options = res + '/' + next
                    print(options)
                elif play.id != 3 or title == '平码':
                    next = '共' + str(len(res.split(','))) + last
                    options = res + '/' + next
                else:
                    n = len(res.split(','))
                    if title == '二中二':
                        sum = int(n * (n - 1) / 2)
                    else:
                        sum = int(n * (n - 1) * (n - 2) / 6)
                    next = '共' + str(sum) + last
                    options = res + '/' + next

                option_id = record_info.option_id
                if option_id:
                    res = Option.objects.get(id=option_id)
                    three_to_two = '三中二'
                    name = res.option
                    if three_to_two in name:
                        name = three_to_two
                    if self.request.GET.get('language') == 'en':
                        three_to_two = 'Three Hit Two'
                        name = res.option_en
                        if three_to_two in name:
                            name = three_to_two
                else:
                    name = record_info.play.title
                    if self.request.GET.get('language') == 'en':
                        name = record_info.play.title_en

                list = {
                    "title": name,
                    "issue": issue,
                    "bet_coin": normalize_fraction((bet_coin/number), int(item['coin_info'].coin_accuracy)),
                    "bets": normalize_fraction(item['bets'], int(item['coin_info'].coin_accuracy)),
                    "options": options
                }
            elif type == 4:  # 股票
                record_info = GuessRecord.objects.get(id=record_id)
                periods = record_info.periods.periods   # 期数
                name = record_info.periods.stock.name    # 股票昵称
                name = str(Stock.STOCK[int(name)][1])   # 玩法昵称
                play_name = str(Play.PLAY[int(record_info.play.play_name)][1])   # 玩法昵称
                options = record_info.options.title   # 选项
                list = {
                    "bets": normalize_fraction(item['bets'], int(item['coin_info'].coin_accuracy)),
                    "periods": periods,
                    "name": name,
                    "options": options,
                    "play_name": play_name
                }
            elif type == 5:   # 股票PK
                record_info = GuesspkRecord.objects.get(id=record_id)

                issue = record_info.issue.issue
                result_answer = record_info.issue.size_pk_result
                left_stock_name = record_info.issue.stock_pk.left_stock_name
                right_stock_name = record_info.issue.stock_pk.right_stock_name
                title = left_stock_name + ' PK ' + right_stock_name
                list = {
                    "bets": normalize_fraction(item['bets'], int(item['coin_info'].coin_accuracy)),
                    "result_answer": result_answer,
                    "option": record_info.option.title,
                    "issue": issue,
                    "title": title
                }
            elif type == 6:
                pass
            elif type == 7:
                pass
            data.append(
                {
                    "user_id": item['user_info']['user_id'],
                    "user_avatar": item['user_info']['user_avatar'],
                    "user_telephone": item['user_info']['user_telephone'],
                    "coin_name": item['coin_info'].name,
                    "source_name": item['source_key'],
                    "source": item['source'],
                    "status": item['status'],
                    "earn_coin": normalize_fraction(item['earn_coin'], int(item['coin_info'].coin_accuracy)),
                    "time": item['time']['time'],
                    "yeas": item['time']['yeas'],
                    "created_ats": item['time']['created_ats'],
                    "list": list
                }
            )
        types = int(self.request.GET.get('type'))
        sum_earn_coin = 0
        sum_bets = 0
        if types == 0 and 'sb_time' not in self.request.GET and 'user_id' in self.request.GET:
            club_id = int(self.request.GET.get("club_id"))
            club_info = Club.objects.get_one(pk=club_id)
            coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
            coin_accuracy = int(coin_info.coin_accuracy)
            user_id = self.request.GET.get('user_id')
            user_list = settings.TEST_USER_ID
            sum_earn_coin = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                           ~Q(status=0),
                                                           user_id=user_id,
                                                           club_id=club_id,
                                                           user__is_block=0).aggregate(Sum('earn_coin'))
            sum__win_earn_coin = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                                ~Q(status=0),
                                                                earn_coin__gt=0,
                                                                user_id=user_id,
                                                                club_id=club_id,
                                                                user__is_block=0).aggregate(Sum('bets'))
            if sum__win_earn_coin['bets__sum'] is None:
                sum__win_earn_coin = 0
            else:
                sum__win_earn_coin = sum__win_earn_coin['bets__sum']
            sum_bets = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                      ~Q(status=0),
                                                      user_id=user_id,
                                                      club_id=club_id,
                                                      user__is_block=0).aggregate(Sum('bets'))
            if sum_bets['bets__sum'] is None:
                sum_bets = 0
            else:
                sum_bets = normalize_fraction(sum_bets['bets__sum'], coin_accuracy)

            if sum_earn_coin['earn_coin__sum'] is None:
                sum_earn_coin = 0
            else:
                sum_earn_coin = sum_earn_coin['earn_coin__sum']
            sum_earn_coin = normalize_fraction((sum_earn_coin - sum__win_earn_coin), coin_accuracy)

        return self.response({"code": 0, "data": data, "sum_bets": sum_bets, "sum_earn_coin": sum_earn_coin})
