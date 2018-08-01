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
    coin = serializers.SerializerMethodField()  # 货币名称
    user_number = serializers.SerializerMethodField()  # 总下注数
    title = serializers.SerializerMethodField()  # 货币头像
    club_autograph = serializers.SerializerMethodField()  # 货币头像

    class Meta:
        model = Club
        fields = ("id", "title", "club_autograph", "user_number", "room_number", "is_recommend", "coin", "icon")

    def get_title(self, obj):  # 货币名称
        room_title = obj.room_title
        if self.context['request'].GET.get('language') == 'en':
            room_title = obj.room_title_en
        return room_title

    def get_club_autograph(self, obj):  # 货币名称
        room_title = obj.autograph
        if self.context['request'].GET.get('language') == 'en':
            room_title = obj.autograph_en
        return room_title

    @staticmethod
    def get_coin(obj):  # 货币
        coin_liat = Coin.objects.get(pk=obj.coin_id)

        # coin_name = coin_liat.name
        # coin_name_key = coin_name.lower()
        # day = datetime.now().strftime('%Y_%m_%d')
        # number_key = "INITIAL_ONLINE_USER_" + str(day)
        # initial_online_user_number = get_cache(number_key)
        # period = number_time_judgment()
        # key_one = "'" + str(period) + "'"
        # # coin_name_key = "'" + str(coin_name_key) + "'"
        # quiz_number = int(initial_online_user_number[period][coin_name_key]['quiz'])
        # guess_number = int(initial_online_user_number[key_one][coin_name_key]['guess'])
        # user_number = quiz_number + guess_number
        # print("user_number=============================", user_number)
        return coin_liat

    @staticmethod
    def get_user_number(obj):
        record_number = Record.objects.filter(roomquiz_id=obj.id).count()
        record_number = int(record_number)*0.3
        return int(record_number)


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
        record_number = 0
        if obj.id == 1:
            record_number = Record.objects.filter(roomquiz_id=club_id).count()
            record_number = record_number * 0.3
        if obj.id == 3:
            record_number = Guess_Record.objects.filter(club_id=club_id).count()
        return int(record_number)


class ClubBannerSerialize(serializers.ModelSerializer):
    """
    轮播图
    """

    class Meta:
        model = ClubBanner
        fields = ('active', 'image')
