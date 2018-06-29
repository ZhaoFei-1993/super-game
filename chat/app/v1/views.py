# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView
from . import serializers
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize
from chat.models import Club
from api.settings import MEDIA_DOMAIN_HOST
from utils.functions import language_switch
from base import code as error_code
from datetime import datetime
from base.exceptions import ParamErrorException


class ClublistView(ListAPIView):
    """
    俱乐部列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = ClubListSerialize

    def get_queryset(self):
        chat_list = Club.objects.filter(is_dissolve=0).order_by('-is_recommend').order_by("-is_recommend")
        return chat_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        user = request.user
        language = self.request.GET.get('language')
        if user.is_block == 1:
            raise ParamErrorException(error_code.API_70203_PROHIBIT_LOGIN)
        data = []
        date_now = datetime.now().strftime('%Y%m%d%H%M')
        int_ban = '/'.join(
            [MEDIA_DOMAIN_HOST, language_switch(self.request.GET.get('language'), "INT_BAN") + ".jpg?t=%s" % date_now])
        usdt_ban = '/'.join(
            [MEDIA_DOMAIN_HOST, language_switch(self.request.GET.get('language'), "USDT") + ".jpg?t=%s" % date_now])
        int_act_ban = '/'.join(
            # [MEDIA_DOMAIN_HOST, language_switch(self.request.GET.get('language'), "INT_ACT") + ".jpg?t=%s" % date_now])
            [MEDIA_DOMAIN_HOST, "INT_ACT.jpg?t=%s" % date_now])
        banner = ([] if language=='en' else [{"img_url": int_ban, "action": 'Invite_New'}]) \
                  + [{"img_url": usdt_ban, "action": 'USDT_ACTIVE'}] \
                  + ([] if language=='en' else [{"img_url": int_act_ban, "action": 'INT_COIN_ACTIVITY'}]) # 活动轮播图
        for item in items:
            user_number = int(int(item['user_number']) * 0.3)
            room_title = language_switch(self.request.GET.get('language'), 'room_title')
            autograph = language_switch(self.request.GET.get('language'), 'autograph')
            room_title = item[room_title]
            autograph = item[autograph]
            data.append(
                {
                    "club_id": item['id'],
                    "room_title": room_title,
                    "autograph": autograph,
                    "user_number": user_number,
                    "room_number": item['room_number'],
                    "coin_name": item['coin_name'],
                    "coin_key": item['coin_key'],
                    "icon": item['icon'],
                    "coin_icon": item['coin_icon'],
                    "is_recommend": item['is_recommend']
                }
            )
        return self.response({"code": 0, "banner": banner, "data": data})
