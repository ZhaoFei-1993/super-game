# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
from django.db.models import Q
from chat.models import ClubRule, Club
from quiz.models import Category
from utils.cache import set_cache, get_cache, decr_cache, incr_cache, delete_cache
from users.models import Coin
import re
import datetime
from utils.functions import normalize_fraction, value_judge, get_sql
from banker.models import BankerBigHeadRecord


class BankerHomeView(ListAPIView):
    """
       联合坐庄：   首页
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        BANKER_RULE_INFO = "BANKER_RULE_INFO"  # 再来一次次数
        # delete_cache(BANKER_RULE_INFO)
        banker_rule_info = get_cache(BANKER_RULE_INFO)
        if banker_rule_info is None:
            quiz_info = Category.objects.filter(Q(id=1) | Q(id=2))
            rule_info = ClubRule.objects.filter(~Q(id__in=[1,4,5,6])).order_by('banker_sort')

            banker_rule_info = []
            a = True
            m = 0
            for i in quiz_info:
                m += 1
                banker_rule_info.append({
                    "type": m,
                    "icon": i.icon,
                    "name": i.name,
                    "stop": a,
                    "order": m
                })

            for s in rule_info:
                id = int(s.id) + 1
                banker_rule_info.append({
                    "type": id,                    # id
                    "icon": s.banker_icon,          # 图片
                    "name": s.title,             # 标题
                    "stop": s.is_banker,              # 是否停止     1.是     2.否
                    "order": s.banker_sort   # 排序
                })
            banker_rule_info = sorted(banker_rule_info, key=lambda x: x['order'], reverse=False)
            set_cache(BANKER_RULE_INFO, banker_rule_info)

        club_info = Club.objects.filter(~Q(is_recommend=0), is_banker=1).order_by("user")
        banker_club_info = []
        for c in club_info:
            coin_info = Coin.objects.get(pk=c.coin_id)
            # coin_info = Coin.objects.get_one(pk=c.coin_id)
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
        club_id = self.request.GET.get('club_id')
        # club_info = Club.objects.get(pk=club_id)
        # club_info = Club.objects.get_one(pk=club_id)
        begin_at = (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        regex = re.compile(r'^(1|2|3|4)$')
        if type is None or not regex.match(type):
            raise ParamErrorException(error_code.API_10104_PARAMETER_EXPIRED)
        if int(type) in (1, 2):      # 1.足球 2.篮球
            if request.GET.get('language') == 'en':
                sql_list = "q.id, q.host_team_en, q.host_team_avatar, q.guest_team_en, q.guest_team_avatar"
            else:
                sql_list = "q.host_team, q.host_team_avatar, q.guest_team, q.guest_team_avatar,"
            sql_list += " date_format( q.begin_at, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( q.begin_at, '%m%d' ) as yeas,"
            sql_list += " date_format( q.begin_at, '%H%i' ) as time"
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
            sql_list = " m.id, m.issue, "
            sql_list += " date_format( m.begin_at, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( m.begin_at, '%m%d' ) as yeas,"
            sql_list += " date_format( m.begin_at, '%H%i' ) as time"
            sql = "select " + sql_list + " from marksix_openprice m"
            sql += " order by created_at desc limit 3"
            list = get_sql(sql)
        else:                # 4.猜股票
            sql_list = " g.id, s.name, "
            sql_list += " date_format( g.lottery_time, '%Y%m%d%H%i%s' ) as times,"
            sql_list += " date_format( g.lottery_time, '%m%d' ) as yeas,"
            sql_list += " date_format( g.lottery_time, '%H%i' ) as time"
            sql = "select " + sql_list + " from guess_periods g"
            sql += " inner join guess_stock s on g.stock_id=s.id"
            sql += " where s.stock_guess_open = 0"
            sql += " and s.is_delete = 0"
            sql += " and g.lottery_time > '" + str(begin_at) + "'"
            sql += " group by s.id"
            sql += " order by times desc limit 4"
            print("sql===============================", sql)
            list = get_sql(sql)

        return self.response({"code": 0})


