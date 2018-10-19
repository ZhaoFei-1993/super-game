# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from base import code as error_code
from base.exceptions import ParamErrorException
from django.db.models import Q
from chat.models import ClubRule, Club
from quiz.models import Category


class BankerRuleView(ListAPIView):
    """
       联合坐庄：   玩法
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        quiz_info = Category.objects.filter(Q(id=2) | Q(id=1))
        rule_info = ClubRule.objects.filter(Q(id=2) | Q(id=3)).order_by('id')

        data = []
        for i in quiz_info:
            data.append({
                "icon": i.icon,
                "name": i.name
            })

        for s in rule_info:
            data.append({
                "icon": s.icon,
                "name": s.title
            })

        return self.response({"code": 0, "data": data})


class BankerClubView(ListAPIView):
    """
        联合坐庄：   俱乐部
    """

    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):

        club_info = Club.objects.filter(~Q(is_recommend=0)).order_by("room_title")

        data = []
        for i in club_info:
            coin_name = i.coin.name
            data.append({
                "icon": i.icon,
                "title": i.coin.name,
                "club_id":i.id,
            })

        return self.response({"code": 0, "data": data})


class BankerDetailView(ListAPIView):
    """
        联合坐庄：   坐庄
    """
    permission_classes = (LoginRequired,)

    def get_queryset(self):
        pass

    def list(self, request, *args, **kwargs):
        club_info = Club.objects.filter(~Q(is_recommend=0)).order_by("room_title")

        data = []
        for i in club_info:
            coin_name = i.coin.name
            data.append({
                "icon": i.icon,
                "title": i.coin.name,
                "club_id": i.id,
            })

        return self.response({"code": 0, "data": data})
