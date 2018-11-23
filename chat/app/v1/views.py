# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize, ClubRuleSerialize, ClubBannerSerialize
from chat.models import Club, ClubRule, ClubBanner
from base import code as error_code
from users.models import UserMessage, DailyLog, Coin, RecordMark
from base.exceptions import ParamErrorException
from django.db.models import Q
from utils.functions import message_hints, number_time_judgment
from datetime import datetime
from utils.cache import get_cache


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
        UserMessage.objects.add_system_user_message(user=user)

        is_sign = DailyLog.objects.is_signed(user.id)  # 是否签到
        is_message = message_hints(user.id)  # 是否有未读消息
        if user.is_block == 1:
            raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)

        # 获取俱乐部货币、在线人数
        coins = Coin.objects.get_coins_map_id()

        data = []
        for item in items:
            club_id = item['id']

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
