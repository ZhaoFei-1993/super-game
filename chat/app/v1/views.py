# -*- coding: UTF-8 -*-
from base.app import ListAPIView
from base.function import LoginRequired
from .serializers import ClubListSerialize, ClubRuleSerialize, ClubBannerSerialize
from chat.models import Club, ClubRule, ClubBanner
from base import code as error_code
from users.models import UserMessage, DailyLog, Coin
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
                chat_list = Club.objects.filter(
                    Q(room_title_en__icontains=name) | Q(room_number__istartswith=name)).order_by('user',
                                                                                                  '-is_recommend')
            else:
                chat_list = Club.objects.filter(
                    Q(room_title__icontains=name) | Q(room_number__istartswith=name)).order_by('user',
                                                                                               '-is_recommend')
        else:
            chat_list = Club.objects.filter(is_dissolve=0).order_by('-is_recommend')
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
            coin = coins[item['coin_id']]
            coin_name = coin.name.lower()
            if coin_name == 'eos':
                user_number = 0
            else:
                day = datetime.now().strftime('%Y-%m-%d')
                number_key = "INITIAL_ONLINE_USER_" + str(day)
                initial_online_user_number = get_cache(number_key)
                period = str(number_time_judgment())
                quiz_number = int(initial_online_user_number[0][period][coin_name]['quiz'])
                guess_number = int(initial_online_user_number[0][period][coin_name]['guess'])
                six_number = int(initial_online_user_number[0][period][coin_name]['six'])
                user_number = quiz_number + guess_number + six_number

            data.append(
                {
                    "club_id": item['id'],
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
            if int(item['id']) == 5:
                data.append(
                    {
                        "clubrule_id": item['id'],
                        "name": item['name'],
                        "icon": item['icon'],
                        "room_number": item['number'],
                        "table_id": 1
                    }
                )
            else:
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
