# -*- coding: UTF-8 -*-
from base.app import ListCreateAPIView
from . import serializers
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize
from chat.models import Club
from wsms import sms
from base import code as error_code
from datetime import datetime
import time
import pytz
from django.conf import settings
from base.exceptions import ParamErrorException


class ClublistView(ListAPIView):
    """
    俱乐部列表
    """
    permission_classes = (LoginRequired,)
    serializer_class = ClubListSerialize

    def get_queryset(self):
        chat_list = Club.objects.filter(is_dissolve=0).order_by('-is_recommend')
        return chat_list

    def list(self, request, *args, **kwargs):
        results = super().list(request, *args, **kwargs)
        items = results.data.get('results')
        data = []
        for item in items:
            data.append(
                {
                    "club_id": item['id'],
                    "room_title": item['room_title'],
                    "autograph": item['autograph'],
                    "user_number": item['user_number'],
                    "room_number": item['room_number'],
                    "coin_name": item['coin_name'],
                    "coin_key": item['coin_key'],
                    "icon": item['icon'],
                    "coin_icon": item['coin_icon'],
                    "is_recommend": item['is_recommend']
                }
            )
        return self.response({"code": 0, "data": data})
