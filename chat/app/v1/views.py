# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize, ClubRuleSerialize, ClubBannerSerialize
from chat.models import Club, ClubRule, ClubBanner
from api.settings import MEDIA_DOMAIN_HOST
from base import code as error_code
from datetime import datetime
from base.exceptions import ParamErrorException
from django.db.models import Q
from utils.functions import sign_confirmation, language_switch, message_hints


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
                chat_list = Club.objects.filter(
                    Q(room_title_en__icontains=name) | Q(room_number__istartswith=name)).order_by('-is_recommend')
            else:
                chat_list = Club.objects.filter(
                    Q(room_title__icontains=name) | Q(room_number__istartswith=name)).order_by(
                    '-is_recommend')
        else:
            chat_list = Club.objects.filter(is_dissolve=0).order_by('-is_recommend')
        return chat_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user = request.user
        is_sign = sign_confirmation(user.id)  # 是否签到
        is_message = message_hints(user.id)  # 是否有未读消息
        if user.is_block == 1:
            raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)
        data = []
        for item in items:
            coin = item['coin'][0]['coin_list']
            data.append(
                {
                    "club_id": item['id'],
                    "room_title": item['title'],
                    "autograph": item['club_autograph'],
                    "user_number": item['coin'][0]['user_number'],
                    "room_number": item['room_number'],
                    "coin_name": coin.name,
                    "coin_key": coin.pk,
                    "icon": item['icon'],
                    "coin_icon": coin.icon,
                    "is_recommend": item['is_recommend']
                }
            )
        content = {"code": 0,
                   "data": data,
                   "is_sign": is_sign,
                   "is_message": is_message
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
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "clubrule_id": item['id'],
                    "name": item['name'],
                    "icon": item['icon'],
                    "room_number": item['number']
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
