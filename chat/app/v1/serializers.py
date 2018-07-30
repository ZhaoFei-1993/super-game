# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import Coin
from chat.models import Club, ClubRule, ClubBanner
from quiz.models import Record
from guess.models import Record as Guess_Record


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
        return coin_liat

    @staticmethod
    def get_user_number(obj):
        record_number = Record.objects.filter(roomquiz_id=obj.pk).count()
        record_number = record_number * 0.3
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
