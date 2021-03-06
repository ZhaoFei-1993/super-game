# -*- coding: UTF-8 -*-
from base.app import ListAPIView, ListCreateAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
from django.db.models import Q, Sum
from chat.models import ClubRule, Club
from quiz.models import Category, Quiz
from marksix.models import OpenPrice
from utils.cache import set_cache, get_cache, decr_cache, incr_cache, delete_cache
from users.models import Coin, UserCoin
from guess.models import Periods
import re
import json
import datetime
from django.db import transaction
from users.models import CoinDetail
from decimal import Decimal
from banker.models import BankerShare, BankerRecord
from utils.functions import get_sql, is_number, normalize_fraction, value_judge, to_decimal
from guess.models import Stock


class BankerHomeView(ListAPIView):
    """
       联合坐庄：   首页
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        BANKER_RULE_INFO = "BANKER_RULE_INFO"  # 缓存
        # delete_cache(BANKER_RULE_INFO)
        banker_rule_info = get_cache(BANKER_RULE_INFO)
        if banker_rule_info is None:
            rule_info = ClubRule.objects.filter(is_banker=True).order_by('banker_sort')

            banker_rule_info = []
            for s in rule_info:
                id = int(s.id)
                if id > 1 and id != 7:
                    id = id + 1
                elif id == 7:
                    id = 2
                banker_rule_info.append({
                    "type": id,  # id
                    "icon": s.banker_icon,  # 图片
                    "name": s.title,  # 标题
                    "stop": s.is_banker,  # 是否停止  1:是 0.否
                    "order": s.banker_sort  # 排序
                })
            banker_rule_info = sorted(banker_rule_info, key=lambda x: x['order'], reverse=False)
            set_cache(BANKER_RULE_INFO, banker_rule_info)

        club_info = Club.objects.filter(~Q(is_recommend=0), is_banker=1).order_by("user")
        banker_club_info = []
        for c in club_info:
            # coin_info = Coin.objects.get(pk=c.coin_id)
            coin_info = Coin.objects.get_one(pk=c.coin_id)
            banker_club_info.append({
                "club_id": c.pk,
                "icon": coin_info.icon,
                "name": coin_info.name,
            })

        return self.response({"code": 0, "banker_rule_info": banker_rule_info, "banker_club_info": banker_club_info})


class BankerInfoView(ListAPIView):
    """
        联合坐庄：  详情
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        type = self.request.GET.get('type')
        club_id = int(self.request.GET.get('club_id'))
        if 'club_id' not in request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        begin_at = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        regex = re.compile(r'^(1|2|3|4)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if int(type) in (1, 2):  # 1.足球 2.篮球
            if request.GET.get('language') == 'en':
                sql_list = "q.id, q.host_team_en, q.host_team_avatar, q.guest_team_en, q.guest_team_avatar"
            else:
                sql_list = "q.id, q.host_team, q.host_team_avatar, q.guest_team, q.guest_team_avatar,"
            sql_list += " date_format( q.begin_at, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( q.begin_at, '%m月%d日' ) as yeas,"
            sql_list += " date_format( q.begin_at, '%H:%i' ) as time"
            sql = "select " + sql_list + " from quiz_quiz q"
            sql += " inner join quiz_category c on q.category_id=c.id"
            if int(type) == 2:
                sql += " where c.parent_id = 1"
            else:
                sql += " where c.parent_id = 2"
            sql += " and q.begin_at > '" + str(begin_at) + "'"
            sql += " order by times"
            list = self.get_list_by_sql(sql)
        elif int(type) == 3:  # 3.六合彩
            sql_list = " m.id, m.next_issue, "
            sql_list += " date_format( m.next_closing, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( m.next_closing, '%m月%d日' ) as yeas,"
            sql_list += " date_format( m.next_closing, '%H:%i' ) as time"
            sql = "select " + sql_list + " from marksix_openprice m"
            sql += " where m.next_closing > '" + str(begin_at) + "'"
            sql += " order by m.next_closing"
            list = get_sql(sql)
        else:  # 4.猜股票
            sql_list = " g.id, s.name, "
            sql_list += " date_format( g.rotary_header_time, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( g.rotary_header_time, '%m月%d日' ) as yeas,"
            sql_list += " date_format( g.rotary_header_time, '%H:%i' ) as time"
            sql = "select " + sql_list + " from guess_periods g"
            sql += " inner join guess_stock s on g.stock_id=s.id"
            sql += " where s.stock_guess_open = 1"
            sql += " and s.is_delete = 0"
            sql += " and g.start_value is null"
            sql += " and g.rotary_header_time > '" + str(begin_at) + "'"
            sql += " order by times"
            print("begin_at==========", begin_at)
            print("sql=====================", sql)
            list = self.get_list_by_sql(sql)
        data = []
        for i in list:
            if int(type) in (1, 2):
                data.append({
                    "key_id": i[0],
                    "host_team": i[1],
                    "host_team_avatar": i[2],
                    "guest_team": i[3],
                    "guest_team_avatar": i[4],
                    "day_time": i[6],
                    "time": i[7]
                })
            elif int(type) == 3:
                if request.GET.get('language') == 'en':
                    name = str("Phase ") + str(i[1])
                else:
                    name = str("第") + str(i[1]) + str("期")
                data.append({
                    "key_id": int(i[0]),
                    "name": name,
                    "day_time": i[3],
                    "time": i[4]
                })
            else:
                if request.GET.get('language') == 'en':
                    name = Stock.STOCK_EN[int(i[1])][1]
                else:
                    name = Stock.STOCK[int(i[1])][1]
                data.append({
                    "key_id": i[0],
                    "name": name,
                    "day_time": i[3],
                    "time": i[4]
                })
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_info.id)

        if 'page_size' in request.GET:
            lists = self.get_all_by_sql(sql)
            page_size = int(self.request.GET.get('page_size'))
            a = len(lists)
            m = a/page_size
            b = a//page_size
            if m == b:
                page = b
            else:
                page = b + 1
        else:
            page = 1
        return self.response({"code": 0,
                              "data": data,
                              "balance": normalize_fraction(user_coin.balance, int(coin_info.coin_accuracy)),
                              "page": page
                              })


class BankerDetailsView(ListAPIView):
    """
       联合坐庄：   认购信息
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        type = self.request.GET.get('type')  # 1.足球 2.篮球  3.六合彩  4.猜股票
        key_id = int(self.request.GET.get('key_id'))  # 玩法对应的key_id
        if is_number(key_id) is False:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        club_id = int(self.request.GET.get('club_id'))
        if 'club_id' not in request.GET:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        regex = re.compile(r'^(1|2|3|4)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        # club_info = Club.objects.get(pk=club_id)
        club_info = Club.objects.get_one(pk=club_id)
        # coin_info = Coin.objects.get(id=club_info.coin_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        coin_name = coin_info.name  # 货币昵称
        coin_icon = coin_info.icon  # 货币图标
        banker_share = BankerShare.objects.filter(club_id=int(club_id), source=int(type)).first()
        sum_share = int(banker_share.balance)  # 份额
        sum_proportion = int(banker_share.proportion * 100)  # 占比

        sql_list = " SUM(r.balance) AS balance, SUM(r.proportion) AS proportion"
        sql = "select " + sql_list + " from banker_bankerrecord r"
        sql += " where r.user_id = '" + str(user.id) + "'"
        sql += " and r.club_id = '" + str(club_id) + "'"
        sql += " and r.key_id = '" + str(key_id) + "'"
        sql += " and r.source = '" + str(type) + "'"
        user_banker = get_sql(sql)[0]
        user_banker_balance = user_banker[0] if user_banker[0] is not None else 0
        user_banker_proportion = user_banker[1] if user_banker[1] is not None else 0

        sql_list = " u.avatar, r.balance, r.proportion"
        sql = "select " + sql_list + " from banker_bankerrecord r"
        sql += " inner join users_user u on r.user_id=u.id"
        sql += " where r.club_id = '" + str(club_id) + "'"
        sql += " and r.key_id = '" + str(key_id) + "'"
        sql += " and r.source = '" + str(type) + "'"
        sql += " order by r.balance desc"
        bamker_list = get_sql(sql)
        user_sum_balance = 0
        user_icon = []
        for i in bamker_list:
            user_sum_balance += i[1]
            user_icon.append({
                "avatar": i[0]
            })
        many_share = sum_share - user_sum_balance
        return self.response({"code": 0,
                              "coin_name": coin_name,
                              "coin_icon": coin_icon,
                              "sum_share": sum_share,
                              "sum_proportion": sum_proportion,
                              "sum_user_number": len(bamker_list),
                              "many_share": normalize_fraction(many_share, int(coin_info.coin_accuracy)),
                              "user_banker_balance": normalize_fraction(user_banker_balance,
                                                                        int(coin_info.coin_accuracy)),  # 用户已购份额
                              "user_banker_proportion": normalize_fraction(user_banker_proportion, 3),  # 用户已购占比
                              "user_icon": user_icon,
                              })


class BankerDetailsTestView(ListCreateAPIView):
    """
    认购信息下校验
    """
    permission_classes = (LoginRequired,)

    def post(self, request, *args, **kwargs):
        user = request.user
        value = value_judge(request, "type", "club_id", "amount", "key_id")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        type = int(self.request.data['type'])  # 玩法类型
        club_id = int(self.request.data['club_id'])  # 俱乐部id
        key_id = int(self.request.data['key_id'])  # 俱乐部id
        amount = to_decimal(self.request.data['amount'])
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_info.id)

        if type == 1 or type == 2:  # 1.足球  2.篮球
            list_info = Quiz.objects.get(id=key_id)
            if int(list_info.status) != 0:
                raise ParamErrorException(error_code.API_110101_USER_BANKER)
        elif type == 3:  # 六合彩
            list_info = OpenPrice.objects.get(id=key_id)
            just_now = datetime.datetime.now() + datetime.timedelta(hours=1)
            next_closing = list_info.next_closing
            if just_now > next_closing:
                raise ParamErrorException(error_code.API_110102_USER_BANKER)
        else:  # 股票
            list_info = Periods.objects.get(id=key_id)
            just_now = datetime.datetime.now() + datetime.timedelta(hours=1)
            rotary_header_time = list_info.rotary_header_time
            if just_now > rotary_header_time:
                raise ParamErrorException(error_code.API_110102_USER_BANKER)

        all_user_gsg = BankerRecord.objects.filter(source=type, key_id=key_id, club_id=club_id).aggregate(Sum('balance'))
        sum_balance = all_user_gsg['balance__sum'] if all_user_gsg['balance__sum'] is not None else 0  # 该局总已认购额
        sum_amount = to_decimal(sum_balance) + amount  # 认购以后该局的总已认购额

        banker_share = BankerShare.objects.filter(club_id=int(club_id), source=int(type)).first()
        sum_share = to_decimal(banker_share.balance)  # 总可购份额

        if sum_amount > sum_share:
            raise ParamErrorException(error_code.API_110103_USER_BANKER)
        if user_coin.balance < amount:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)
        return self.response({"code": 0})


class BankerBuyView(ListCreateAPIView):
    """
    联合坐庄：   确认做庄
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        user = request.user
        value = value_judge(request, "type", "club_id", "list")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        type = self.request.data['type']  # 玩法类型
        regex = re.compile(r'^(1|2|3|4)$')  # 1.足球 2.篮球  3.六合彩  4.猜股票
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        type = int(type)
        club_id = int(self.request.data['club_id'])  # 俱乐部id
        data = self.request.data['list']  # key_id
        data = json.loads(str(data))
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_info.id)
        coin_accuracy = int(coin_info.coin_accuracy)
        if club_info.is_banker is False:
            raise ParamErrorException(error_code.API_110104_USER_BANKER)

        info = []
        new_sum_balance = 0

        for i in data:
            amount = i["amount"]
            amount = normalize_fraction(amount, 5)
            print("amount==================", amount)
            key_id = int(i["key_id"])

            if amount <= 0:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

            if type == 1 or type == 2:  # 1.足球  2.篮球
                list_info = Quiz.objects.get(id=key_id)
                if int(list_info.status) != 0:
                    raise ParamErrorException(error_code.API_110101_USER_BANKER)
            elif type == 3:  # 六合彩
                list_info = OpenPrice.objects.get(id=key_id)
                just_now = datetime.datetime.now() + datetime.timedelta(hours=1)
                next_closing = list_info.next_closing
                if just_now > next_closing:
                    raise ParamErrorException(error_code.API_110102_USER_BANKER)
            else:  # 股票
                list_info = Periods.objects.get(id=key_id)
                just_now = datetime.datetime.now() + datetime.timedelta(hours=1)
                rotary_header_time = list_info.rotary_header_time
                if just_now > rotary_header_time:
                    raise ParamErrorException(error_code.API_110102_USER_BANKER)

            all_user_gsg = BankerRecord.objects.filter(source=type, key_id=key_id, club_id=club_id).aggregate(Sum('balance'))
            sum_balance = all_user_gsg['balance__sum'] if all_user_gsg['balance__sum'] is not None else 0  # 该局总已认购额
            print("sum_balance==================", sum_balance)
            sum_amount = to_decimal(sum_balance) + amount  # 认购以后该局的总已认购额

            banker_share = BankerShare.objects.filter(club_id=int(club_id), source=int(type)).first()
            sum_share = to_decimal(banker_share.balance)  # 总可购份额

            info.append({
                "key_id": key_id,
                "sum_amount": sum_amount,
                "sum_share": to_decimal(sum_share),
                "amount": to_decimal(amount)
            })

            print("sum_amount==================", sum_amount)
            print("sum_share==================", sum_share)
            if sum_amount > sum_share:
                raise ParamErrorException(error_code.API_110103_USER_BANKER)
            new_sum_balance += amount
        if user_coin.balance < new_sum_balance:
            raise ParamErrorException(error_code.API_50104_USER_COIN_NOT_METH)

        for s in info:
            banker_record = BankerRecord()
            banker_record.club = club_info
            banker_record.user = user
            banker_record.balance = s["amount"]
            print("amount==============", s["amount"])
            print("sum_share==============", s["sum_share"])
            proportion = normalize_fraction(s["amount"] / s["sum_share"], 4)
            print("proportion===============", proportion)
            banker_record.proportion = to_decimal(proportion)
            banker_record.source = type
            banker_record.key_id = s["key_id"]
            banker_record.save()

        user_coin.balance -= to_decimal(new_sum_balance)
        user_coin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = coin_info.name
        coin_detail.amount = to_decimal('-' + str(new_sum_balance))
        coin_detail.rest = user_coin.balance
        coin_detail.sources = 18
        coin_detail.save()

        return self.response({'code': 0, "balance": normalize_fraction(user_coin.balance, coin_accuracy)})


class BankerRecordView(ListAPIView):
    """
       联合坐庄：   投注记录
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user = self.request.user
        type = self.request.GET.get('type')  # 1.足球 2.篮球  3.六合彩  4.猜股票

        regex = re.compile(r'^(1|2|3|4)$')  # 1.足球 2.篮球  3.六合彩  4.猜股票
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        type = int(type)
        sql_list = "r.club_id, r.source, r.proportion, r.status, r.balance, r.earn_coin, r.created_at,"
        sql_list += "  date_format(r.created_at, '%Y') as yearss, date_format( r.created_at, '%c/%e' ) as years,"
        sql_list += " date_format( r.created_at, '%k:%i' ) as time,"
        if type in (1, 2):
            if request.GET.get('language') == 'en':
                sql_list += " q.host_team_en, q.guest_team_en, r.key_id, date_format( q.begin_at, '%m/%d' ) as times"
            else:
                sql_list += " q.host_team, q.guest_team, r.key_id, date_format( q.begin_at, '%m/%d' ) as times"
        elif type == 3:
            sql_list += " q.next_issue, r.key_id"
        elif type == 4:
            sql_list += " s.name, r.key_id, date_format( q.lottery_time, '%m/%d' ) as times"

        sql = "select " + sql_list + " from banker_bankerrecord r"
        if type in (1, 2):
            sql += " inner join quiz_quiz q on r.key_id=q.id"
        elif type == 3:
            sql += " inner join marksix_openprice q on r.key_id=q.id"
        elif type == 4:
            sql += " inner join guess_periods q on r.key_id=q.id"
            sql += " inner join guess_stock s on q.stock_id=s.id"
        sql += " where r.user_id = '" + str(user.id) + "'"
        if "club_id" in self.request.GET:
            club_id = str(self.request.GET.get('club_id'))  # 俱乐部id
            sql += " and r.club_id = '" + club_id + "'"
        sql += " and r.source = '" + str(type) + "'"
        sql += " order by r.created_at desc"
        banker_list = self.get_list_by_sql(sql)

        data = []
        tmp = ""
        for i in banker_list:
            status = int(i[3])
            name = ""
            key_id = ""
            if type in (1, 2):
                name = str(i[10]) + " VS " + str(i[11]) + " " + str(i[13])

                key_id = int(i[12])
            elif type == 3:
                if request.GET.get('language') == 'en':
                    name = str("Phase ") + str(i[10])
                    key_id = int(i[11])
                else:
                    name = str("第") + str(i[10]) + str("期")
                    key_id = int(i[11])
            elif type == 4:
                if request.GET.get('language') == 'en':
                    name = Stock.STOCK_EN[int(i[10])][1]
                    name = str(name) + " " + str(i[12])
                    key_id = int(i[11])
                else:
                    name = Stock.STOCK[int(i[10])][1]
                    name = str(name) + " " + str(i[12])
                    key_id = int(i[11])

            # club_info = Club.objects.get(id=int(i.club_id))
            club_info = Club.objects.get_one(pk=int(i[0]))
            # coin_info = Coin.objects.get(id=int(club_info.coin_id))
            coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
            coin_accuracy = int(coin_info.coin_accuracy)
            rule = BankerRecord.SOURCE[int(i[1])-1][1]

            print("i[2]=================", i[2])
            print("i[2]=================", i[2] * 100)
            proportion = i[2] * 100 * to_decimal(0.4)
            print("proportion=================", proportion)
            proportion = normalize_fraction(proportion, 2)
            print("proportion===============", proportion)
            proportion = str(proportion) + "%"
            print("proportion================", proportion)

            earn_coin = normalize_fraction(i[5], coin_accuracy)
            if status not in (1, 3):
                if earn_coin > 0:
                    earn_coin = "+" + str(earn_coin)
                    status = 2
                else:
                    if to_decimal(earn_coin) < to_decimal("-" + str(i[4])):
                        earn_coin = normalize_fraction(to_decimal(i[4]), coin_accuracy)
                        earn_coin = "-" + str(earn_coin)
                    earn_coin = str(earn_coin)
                    status = 4

            years = i[7]
            date = i[8]
            if tmp == date:
                date = ""
                years = ""
            else:
                tmp = date
            data.append({
                "rule": rule,  # 玩法
                "club_name": club_info.room_title,  # 俱乐部标题
                "key_id": key_id,  # key_id
                "club_id": int(i[0]),  # 俱乐部id
                "coin_icon": coin_info.icon,  # 货币图标
                "coin_name": coin_info.name,  # 货币昵称
                "earn_coin": earn_coin,  # 获得金额
                "proportion": proportion,  # 占比
                "name": name,  # 占比
                "time": i[9],  # 时:分
                "years": years,  # 年
                "date": date,  # 月/日
                "balance": normalize_fraction(i[4], coin_accuracy),  # 认购金额
                "status": status  # 1.待结算 2.赢 3.流盘 4.输
            })
        return self.response({"code": 0, "data": data})


class BankerClubView(ListAPIView):
    """
    记录下俱乐部
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        user_id = str(self.request.user.id)
        type = self.request.GET.get("type")
        data = []
        sql_list = " cc.id, c.icon, count(cc.id) as number"

        sql = "select " + sql_list + " from banker_bankerrecord r"
        sql += " inner join chat_club cc on r.club_id=cc.id"
        sql += " inner join users_coin c on cc.coin_id=c.id"
        sql += " where r.user_id = '" + str(user_id) + "'"
        sql += " and r.source = '" + str(type) + "'"
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


class AmountDetailsView(ListAPIView):
    """
    投注流水
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        type = int(self.request.GET.get("type"))
        club_id = self.request.GET.get("club_id")
        club_info = Club.objects.get_one(pk=int(club_id))
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        key_id = self.request.GET.get("key_id")
        data = []
        sql_list = "date_format( r.created_at, '%k:%i' ) as time, r.bets, u.telephone, u.area_code, u.nickname"
        sql_list += ", r.created_at"

        sql = "select " + sql_list + " from promotion_promotionrecord r"
        sql += " inner join chat_club cc on r.club_id=cc.id"
        sql += " inner join users_coin c on cc.coin_id=c.id"
        sql += " inner join users_user u on r.user_id=u.id"
        if type in (1, 2):
            sql += " inner join quiz_record q on r.record_id=q.id"
        elif type == 3:
            sql += " inner join marksix_sixrecord q on r.record_id=q.id"
        elif type == 4:
            sql += " inner join guess_record q on r.record_id=q.id"

        sql += " where r.club_id = '" + str(club_id) + "'"
        if type in (1, 2):
            sql += " and q.quiz_id = '" + str(key_id) + "'"
        elif type == 3:
            sql += " and q.open_price_id = '" + str(key_id) + "'"
        elif type == 4:
            sql += " and q.periods_id = '" + str(key_id) + "'"

        sql += " and r.source = '" + str(type) + "'"
        sql += " and u.is_robot = 0"
        sql += " order by r.created_at desc"
        print(sql)
        list = self.get_list_by_sql(sql)
        sum_bet = 0
        for i in list:
            sum_bet += to_decimal(i[1])
            nickname = str(i[2][0:3]) + "***" + str(i[2][7:])
            f = len(str(i[4]))
            if f > 1:
                fs = f - 1
                telephone = str(i[4][0:1]) + "***" + str(i[4][fs:f])
            else:
                telephone = str(i[4][0:1]) + "***"
            data.append({
                "telephone": nickname,
                "coin_icon": coin_info.icon,
                "coin_name": coin_info.name,
                "time": i[0],
                "bets": normalize_fraction(i[1], coin_info.coin_accuracy),
                "area_code": i[3],
                "nickname": telephone,
            })
        return self.response({"code": 0, "data": data, "sum_bet": normalize_fraction(sum_bet, coin_info.coin_accuracy)})

