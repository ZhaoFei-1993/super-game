# -*- coding: UTF-8 -*-
from base.app import ListAPIView, CreateAPIView, ListCreateAPIView
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
from utils.functions import  get_sql, is_number, normalize_fraction, value_judge
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
            rule_info = ClubRule.objects.filter(id__in=[1, 2, 7]).order_by('banker_sort')

            banker_rule_info = []
            for s in rule_info:
                id = int(s.id)
                if id > 1 and id != 7:
                    id = id + 1
                elif id == 7:
                    id = 2
                banker_rule_info.append({
                    "type": id,                    # id
                    "icon": s.banker_icon,          # 图片
                    "name": s.title,             # 标题
                    "stop": s.is_banker,        # 是否停止  1:是 0.否
                    "order": s.banker_sort   # 排序
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
        # club_info = Club.objects.get(pk=club_id)
        club_info = Club.objects.get_one(pk=club_id)
        # coin_info = Coin.objects.get(pk=club_info.coin.id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        begin_at = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        regex = re.compile(r'^(1|2|3|4)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if int(type) in (1, 2):      # 1.足球 2.篮球
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
            sql += " order by times desc"
            list = self.get_list_by_sql(sql)
        elif type == 3:        # 3.六合彩
            sql_list = " m.id, m.next_issue, "
            sql_list += " date_format( m.next_closing, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( m.next_closing, '%m月%d日' ) as yeas,"
            sql_list += " date_format( m.next_closing, '%H:%i' ) as time"
            sql = "select " + sql_list + " from marksix_openprice m"
            sql += " order by created_at desc limit 3"
            list = self.get_list_by_sql(sql)
        else:                # 4.猜股票
            sql_list = " g.id, s.name, "
            sql_list += " date_format( g.rotary_header_time, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( g.rotary_header_time, '%m月%d日' ) as yeas,"
            sql_list += " date_format( g.rotary_header_time, '%H:%i' ) as time"
            sql = "select " + sql_list + " from guess_periods g"
            sql += " inner join guess_stock s on g.stock_id=s.id"
            sql += " where s.stock_guess_open = 0"
            sql += " and s.is_delete = 0"
            sql += " and g.start_value is null"
            sql += " and g.rotary_header_time > '" + str(begin_at) + "'"
            sql += " order by times desc"
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
                    "key_id": i[0],
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

        return self.response({"code": 0,
                              "data": data,
                              "balance": normalize_fraction(user_coin.balance, int(coin_info.coin_accuracy))
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
        type = self.request.GET.get('type')   # 1.足球 2.篮球  3.六合彩  4.猜股票
        key_id = int(self.request.GET.get('key_id'))       # 玩法对应的key_id
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
        coin_name = coin_info.name   # 货币昵称
        coin_icon = coin_info.icon   # 货币图标
        banker_share = BankerShare.objects.filter(club_id=int(club_id), source=int(type)).first()
        sum_share = int(banker_share.balance)   # 份额
        sum_proportion = int(banker_share.proportion*100)   # 占比

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
                              "many_share": normalize_fraction(many_share,
                                                 int(coin_info.coin_accuracy)),
                              "user_banker_balance": normalize_fraction(user_banker_balance,
                                                                        int(coin_info.coin_accuracy)),   # 用户已购份额
                              "user_banker_proportion": normalize_fraction(user_banker_proportion, 3),   # 用户已购占比
                              "user_icon": user_icon,
                            })


class BankerBuyView(ListCreateAPIView):
    """
          联合坐庄：   确认做庄
    """
    permission_classes = (LoginRequired,)

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        user = request.user
        value = value_judge(request, "type", "club_id", "data")
        if value == 0:
            raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)
        type = self.request.data['type']  # 玩法类型
        regex = re.compile(r'^(1|2|3|4)$')      # 1.足球 2.篮球  3.六合彩  4.猜股票
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        type = int(type)
        club_id = int(self.request.data['club_id'])  # 俱乐部id
        data = self.request.data['data']  # key_id
        data = json.loads(str(data))
        # club_info = Club.objects.get(pk=club_id)
        club_info = Club.objects.get_one(pk=club_id)
        # coin_info = Coin.objects.get(id=club_info.coin_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin.id))
        user_coin = UserCoin.objects.get(user_id=user.id, coin_id=coin_info.id)
        coin_accuracy = int(coin_info.coin_accuracy)

        info = []
        new_sum_balance = 0

        for i in data:
            amount = Decimal(i["amount"])
            key_id = int(i["key_id"])

            if amount <= 0:
                raise ParamErrorException(error_code.API_405_WAGER_PARAMETER)

            if type == 1 or type == 2:  # 1.足球  2.篮球
                list_info = Quiz.objects.get(id=key_id)
                if int(list_info.status) != 0:
                    raise ParamErrorException(error_code.API_110101_USER_BANKER)
            elif type == 3:  # 六合彩
                list_info = OpenPrice.objects.get(id=key_id)
                next_closing = list_info.next_closing + datetime.timedelta(hours=1)
                if datetime.datetime.now() > next_closing:
                    raise ParamErrorException(error_code.API_110102_USER_BANKER)
            else:  # 股票
                list_info = Periods.objects.get(id=key_id)
                rotary_header_time = list_info.rotary_header_time + datetime.timedelta(hours=1)
                if datetime.datetime.now() > rotary_header_time:
                    raise ParamErrorException(error_code.API_110102_USER_BANKER)

            all_user_gsg = BankerRecord.objects.filter(source=type, key_id=key_id).aggregate(Sum('balance'))
            sum_balance = all_user_gsg['balance__sum'] if all_user_gsg['balance__sum'] is not None else 0  # 该局总已认购额
            sum_amount = Decimal(sum_balance) + amount   # 认购以后该局的总已认购额

            banker_share = BankerShare.objects.filter(club_id=int(club_id), source=int(type)).first()
            sum_share = Decimal(banker_share.balance)  # 总可购份额

            info.append({
                "key_id": key_id,
                "sum_amount": sum_amount,
                "sum_share": Decimal(sum_share),
                "amount": Decimal(amount)
            })

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
            proportion = normalize_fraction(s["amount"]/s["sum_share"], 2)
            print("proportion===============", proportion)
            banker_record.proportion = Decimal(proportion)
            banker_record.source = type
            banker_record.key_id = s["key_id"]
            banker_record.save()

        user_coin.balance -= Decimal(new_sum_balance)
        user_coin.save()

        coin_detail = CoinDetail()
        coin_detail.user = user
        coin_detail.coin_name = coin_info.name
        coin_detail.amount = Decimal('-' + str(new_sum_balance))
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
                sql_list += " q.host_team_en, q.guest_team_en"
            else:
                sql_list += " q.host_team, q.guest_team"
        elif type == 3:
            sql_list += " q.next_issue"
        elif type == 4:
            sql_list += " s.name"

        sql = "select " + sql_list + " from banker_bankerrecord r"
        if type in (1, 2):
            sql += " inner join quiz_quiz q on r.key_id=q.id"
        elif type == 3:
            sql += " inner join marksix_openprice q on r.key_id=q.id"
        elif type == 4:
            sql += " inner join guess_periods q on r.key_id=q.id"
            sql += " inner join guess_stock s on q.stock_id=s.id"
        sql += " where r.user_id = '" + str(user.id) + "'"
        sql += " and r.source = '" + str(type) + "'"
        sql += " order by r.created_at desc"
        banker_list = self.get_list_by_sql(sql)

        data = []
        tmp = ""
        for i in banker_list:
            name = ""
            if type in (1, 2):
                name = str(i[10]) + " VS " + str(i[11])
            elif type == 3:
                if request.GET.get('language') == 'en':
                    name = str("Phase ") + str(i[10])
                else:
                    name = str("第") + str(i[10]) + str("期")
            elif type == 4:
                if request.GET.get('language') == 'en':
                    name = Stock.STOCK_EN[int(i[10])][1]
                else:
                    name = Stock.STOCK[int(i[10])][1]

            # club_info = Club.objects.get(id=int(i.club_id))
            club_info = Club.objects.get_one(pk=int(i[0]))
            # coin_info = Coin.objects.get(id=int(club_info.coin_id))
            coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
            coin_accuracy = int(coin_info.coin_accuracy)
            rule = BankerRecord.SOURCE[int(i[1])][1]

            proportion = i[2] * 100 * Decimal(0.4)
            proportion = normalize_fraction(proportion, 2)
            proportion = str(proportion) + "%"

            earn_coin = normalize_fraction(i[5], coin_accuracy)
            if earn_coin > 0:
                earn_coin = "+ " + str(earn_coin)
            else:
                earn_coin = "- " + str(earn_coin)

            years = i[7]
            date = i[8]
            if tmp == date:
                date = ""
                years = ""
            else:
                tmp = date
            data.append({
                "rule": rule,     # 玩法
                "club_name": club_info.room_title,   # 俱乐部标题
                "coin_icon": coin_info.icon,   # 货币图标
                "coin_name": coin_info.name,    # 货币昵称
                "earn_coin": earn_coin,   # 获得金额
                "proportion": proportion,     # 占比
                "name": name,     # 占比
                "time": i[9],     # 时:分
                "years": years,     # 年
                "date": date,     # 月/日
                "balance": normalize_fraction(i[4], coin_accuracy),   # 认购金额
                "status": int(i[3])   # 1.待结算 2.已结算 3.流盘
            })
        return self.response({"code": 0, "data": data})



