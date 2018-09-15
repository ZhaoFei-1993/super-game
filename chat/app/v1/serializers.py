# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import Coin
from chat.models import Club, ClubRule, ClubBanner
from quiz.models import Record
from guess.models import Record as Guess_Record
from datetime import datetime
from utils.functions import number_time_judgment
from utils.cache import get_cache, set_cache, delete_cache


class ClubListSerialize(serializers.ModelSerializer):
    """
    序列号
    """
    title = serializers.SerializerMethodField()  # 货币头像
    club_autograph = serializers.SerializerMethodField()  # 货币头像

    class Meta:
        model = Club
        fields = ("id", "title", "club_autograph", "room_number", "is_recommend", "coin_id", "icon")

    def get_title(self, obj):  # 俱乐部名称
        room_title = obj.room_title
        if self.context['request'].GET.get('language') == 'en':
            room_title = obj.room_title_en
        return room_title

    def get_club_autograph(self, obj):  # 俱乐部签名
        room_title = obj.autograph
        if self.context['request'].GET.get('language') == 'en':
            room_title = obj.autograph_en
        return room_title


class ClubRuleSerialize(serializers.ModelSerializer):
    """
    玩法序列化
    """
    name = serializers.SerializerMethodField()  # 玩法昵称
    number = serializers.SerializerMethodField()  # 玩法昵称

    class Meta:
        model = ClubRule
        fields = ("id", "name", "number", "icon")

    def get_name(self, obj):  # 货币名称
        name = obj.title
        if self.context['request'].GET.get('language') == 'en':
            name = obj.title_en
        return name

    def get_number(self, obj):
        club_id = self.context['request'].GET.get('club_id')
        club_liat = Club.objects.get(pk=club_id)

        coin_name = club_liat.coin.name
        coin_name_key = str(coin_name.lower())
        day = datetime.now().strftime('%Y-%m-%d')
        number_key = "INITIAL_ONLINE_USER_" + str(day)
        initial_online_user_number = get_cache(number_key)
        period = str(number_time_judgment())
        print('initial_online_user_number = ', initial_online_user_number)
        print('period = ', period)
        print('coin_name_key = ', coin_name_key)
        if int(obj.id) == 1:
            user_number = int(initial_online_user_number[0][period][coin_name_key]['quiz'])
        elif int(obj.id) == 3:
            user_number = int(initial_online_user_number[0][period][coin_name_key]['guess'])
        elif int(obj.id) == 2:
            user_number = int(initial_online_user_number[0][period][coin_name_key]['six'])
        elif int(obj.id) == 4:
            user_number = int(initial_online_user_number[0][period][coin_name_key]['lhd'])
        else:
            user_number = int(initial_online_user_number[0][period][coin_name_key]['bjl'])
        return user_number


class ClubBannerSerialize(serializers.ModelSerializer):
    """
    轮播图
    """

    class Meta:
        model = ClubBanner
        fields = ('active', 'image', 'banner_type', 'param', 'title')
