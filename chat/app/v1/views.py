# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize, ClubRuleSerialize, ClubBannerSerialize
from chat.models import Club, ClubRule, ClubBanner, ClubIdentity
from users.models import User
from base import code as error_code
from base.exceptions import ParamErrorException
from users.models import UserMessage, DailyLog, Coin, RecordMark, UserRecharge, UserPresentation, UserCoin
from django.db.models import Q
from utils.functions import message_hints, normalize_fraction, get_sql
from django.db.models import Sum
import datetime
import calendar
from decimal import Decimal
from datetime import timedelta
from django.conf import settings
from utils.cache import get_cache, set_cache, delete_cache
from promotion.models import PromotionRecord
from django.db import connection
from promotion.models import UserPresentation as Promotion


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
            is_identity = ClubIdentity.objects.filter(is_deleted=0, user_id=int(user.id), club_id=club_id).count()
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
                    "is_identity": is_identity,
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
        club_id = int(request.GET.get("club_id"))
        coin_id = int(Club.objects.get_one(pk=club_id).coin_id)
        print(coin_id)
        user_list = str(settings.TEST_USER_IDS)

        sql_list = " u.id, u.area_code, u.telephone, u.is_block, date_format( u.created_at, '%Y-%m-%d' ) as time,"
        if type == 1: # 登陆
            sql_list += " (select l.login_time from users_loginrecord l where l.user_id=u.id " \
                        "order by l.login_time desc limit 1) as sb_time"
        else:    # 激活
            sql_list += " max(ur.created_at) as sb_time"
        sql = "select " + sql_list + " from users_userrecharge ur"
        sql += " inner join users_user u on ur.user_id=u.id"
        sql += " where u.is_robot = 0"
        sql += " and u.id not in " + user_list
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
        day = datetime.datetime.now().strftime('%Y-%m-%d')
        day_start = str(day) + " 00:00:00"
        day_end = str(day) + " 23:59:59"
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_start = str(yesterday) + ' 00:00:00'
        yesterday_end = str(yesterday) + ' 23:59:59'

        club_id = int(self.request.GET.get("club_id"))
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

        sum_list = Promotion.objects.filter(~Q(user_id__in=user_list),
                                            club_id=int(club_id), user__is_block=0).aggregate(Sum('bet_water'))
        if sum_list['bet_water__sum'] is None:
            sum_bet_water = 0
        else:
            sum_bet_water = normalize_fraction(sum_list['bet_water__sum'], coin_accuracy)       # 总投注流水

        sum_list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                  earn_coin__gt=0,
                                                  club_id=int(club_id), user__is_block=0).aggregate(Sum('earn_coin'))
        # 赔的钱
        sum_lists = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                   earn_coin__lt=0,
                                                   club_id=int(club_id), user__is_block=0).aggregate(Sum('earn_coin'))
        # 赚的钱
        sum_win_list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                      club_id=int(club_id),
                                                      earn_coin__gt=0, user__is_block=0).aggregate(Sum('bets'))
        # 应扣除的本金

        if sum_win_list['bets__sum'] is None:
            sum_betss = 0
        else:
            sum_betss = sum_win_list['bets__sum']     # 应扣除的本金

        if sum_list['earn_coin__sum'] is None:
            sum_bets = 0
        else:
            sum_bets = sum_list['earn_coin__sum']      # 赔的钱
        sum_bets = sum_bets - sum_betss
        sum_bets = Decimal('-' + str(sum_bets))

        if sum_lists['earn_coin__sum'] is None:
            sum_win_bets = 0
        else:
            sum_win_bets = sum_lists['earn_coin__sum'] * Decimal(0.95)    # 赚的钱
        sum_bets = sum_bets + abs(sum_win_bets)

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
        club_id = int(request.GET.get("club_id"))
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

        month_id = int(self.request.GET.get("month_id"))
        club_id = int(self.request.GET.get("club_id"))
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
        user_lists = settings.TEST_USER_ID

        key = "MONTH_BET_LIST_" + str(club_id) + "_" + str(month_month) + str(type)
        delete_cache(key)
        list = get_cache(key)
        if list is None:
            sql_list = "date_format( p.created_at, '%Y年%m月%d日' ) as years, sum(p.bets), "
            sql_list += "SUM((CASE WHEN p.earn_coin > 0 THEN 0 ELSE p.earn_coin END)) AS earn_coin, "
            sql_list += "date_format( p.created_at, '%Y%m%d' ) as time, date_format( p.created_at, '%Y-%m-%d' ) as sb, "
            sql_list += "SUM((CASE WHEN p.earn_coin > 0 THEN p.bets ELSE 0 END)) AS earn_coins, "
            sql_list += "SUM((CASE WHEN p.earn_coin > 0 THEN p.earn_coin ELSE 0 END)) AS earn_coinss"
            sql = "select " + sql_list + " from promotion_promotionrecord p"
            sql += " inner join users_user u on p.user_id=u.id"
            sql += " where p.club_id = '" + str(club_id) + "'"
            sql += " and p.status != 2"
            sql += " and p.user_id not in " + user_list
            sql += " and u.is_robot = 0"
            sql += " and p.created_at >= '" + str(month_start) + "'"
            sql += " and p.created_at <= '" + str(month_end) + "'"
            sql += "group by years, sb, time"
            sql += " order by time desc"
            list_info = get_sql(sql)
            list = []
            for i in list_info:
                if i[2] is None:
                    earn_coin = 0
                else:
                    earn_coin = Decimal(i[2])   # 总赢
                    earn_coin = Decimal(abs(earn_coin * Decimal(0.95)))
                print("earn_coi=============", earn_coin)
                if i[5] is None:
                    bet_coin = 0
                else:
                    bet_coin = Decimal(i[5])   # 本金
                print("bet_coin==================", bet_coin)
                if i[6] is None:
                    win_coin = 0
                else:
                    win_coin = Decimal(i[6])   # 总亏
                    win_coin = Decimal("-" + str(win_coin))
                print("win_coin==================", win_coin)
                earn_coin = earn_coin + win_coin - bet_coin
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
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        coin_accuracy = int(coin_info.coin_accuracy)

        user_list = str(settings.TEST_USER_IDS)

        sql_list = "date_format( p.created_at, '%Y年%m月' ) as years, "
        sql_list += "SUM((CASE WHEN p.earn_coin > 0 THEN p.earn_coin - p.bets ELSE p.earn_coin END)) AS earn_coin, "
        sql_list += "date_format( p.created_at, '%Y%m' ) as time"
        sql = "select " + sql_list + " from promotion_promotionrecord p"
        sql += " inner join users_user u on p.user_id=u.id"
        sql += " where p.club_id = '" + str(club_id) + "'"
        sql += " and p.user_id not in " + user_list
        sql += " and p.status = 1"
        sql += " and u.is_robot = 0"
        sql += " group by years, time"
        sql += " order by time desc"
        print("sql==========", sql)
        list_info = get_sql(sql)
        list = []
        for i in list_info:
            earn_coin = Decimal(i[1])
            if earn_coin < 0:
                earn_coin = Decimal(abs(earn_coin * Decimal(0.95)))
            if earn_coin > 0:
                earn_coin = Decimal("-" + str(earn_coin))
            list.append({
                "time": i[0],
                "earn_coin": normalize_fraction(earn_coin, coin_accuracy)
            })
        return self.response({"code": 0, "list": list})


class PayClubView(ListAPIView):
    """
    俱乐部充值提现明细
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user

        month_id = int(self.request.GET.get("month_id"))
        club_id = int(self.request.GET.get("club_id"))
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
                                                               created_at__lte=month_end).values('user_id').count()  # 当月总充值人数
        else:
            recharge_user_number = UserPresentation.objects.filter(~Q(user_id__in=user_list),
                                                                   coin_id=int(coin_info.id),
                                                                   created_at__gte=month_start,
                                                                   created_at__lte=month_end).values('user_id').count()

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


class ClubDayBetView(ListAPIView):
    """
    单天投注记录
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user

        sb_time = str(self.request.GET.get("sb_time"))
        start = sb_time + " 00:00:00"
        end = sb_time + " 23:59:59"

        club_id = int(self.request.GET.get("club_id"))
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

        number = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                club_id=int(club_id), created_at__gte=start, source=type,
                                                created_at__lte=end, user__is_block=0
                                                ).values('user_id').distinct().count()
        sum_bets = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                  club_id=int(club_id), created_at__gte=start, source=type,
                                                  created_at__lte=end, user__is_block=0).aggregate(Sum('bets'))

        sum_list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                  club_id=int(club_id),
                                                  earn_coin__gt=0, created_at__gte=start, created_at__lte=end,
                                                  source=type, user__is_block=0).aggregate(Sum('earn_coin'))
        # 赔的钱
        sum_lists = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                   club_id=int(club_id),
                                                   earn_coin__lt=0,
                                                   created_at__gte=start,
                                                   created_at__lte=end,
                                                   source=type, user__is_block=0).aggregate(Sum('earn_coin'))
        # 赚的钱
        sum_win_list = PromotionRecord.objects.filter(~Q(user_id__in=user_list),
                                                      earn_coin__gt=0,
                                                      club_id=int(club_id),
                                                      created_at__gte=start,
                                                      created_at__lte=end,
                                                      source=type, user__is_block=0).aggregate(Sum('bets'))
        # 应该扣的本金

        if sum_bets['bets__sum'] is None:
            sum_bets = 0
        else:
            sum_bets = normalize_fraction(sum_bets['bets__sum'], coin_accuracy)  # 总投注流水

        if sum_win_list['bets__sum'] is None:
            sum_betss = 0
        else:
            sum_betss = sum_win_list['bets__sum']  # 应扣除的本金

        if sum_list['earn_coin__sum'] is None:
            sum_bets_list = 0
        else:
            sum_bets_list = sum_list['earn_coin__sum']  # 赔的钱
        sum_bets_list = sum_bets_list - sum_betss
        sum_bets_list = Decimal('-' + str(sum_bets_list))

        if sum_lists['earn_coin__sum'] is None:
            sum_earn_coin = 0
        else:
            sum_earn_coin = sum_lists['earn_coin__sum'] * Decimal(0.95)  # 赚的钱
        sum_earn_coin = sum_bets_list + abs(sum_earn_coin)
        sum_earn_coin = normalize_fraction(sum_earn_coin, coin_accuracy)  # 总分红

        return self.response({"code": 0,
                              "number": number,
                              "sum_bets": sum_bets,
                              "sum_earn_coin": sum_earn_coin,
                              "coin_name": coin_info.name})
