# -*- coding: UTF-8 -*-
from rest_framework import serializers
from chat.models import Club, ClubRule, ClubBanner


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
    name = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()

    class Meta:
        model = ClubRule
        fields = ("id", "name", "number", "icon")

    def get_name(self, obj):
        """
        玩法名称
        :param obj:
        :return:
        """
        name = obj.title
        if self.context['request'].GET.get('language') == 'en':
            name = obj.title_en
        return name

    def get_number(self, obj):
        """
        在线人数
        :param obj:
        :return:
        """
        club_id = self.context['request'].GET.get('club_id')
        play_id = obj.id

        user_number = Club.objects.get_club_online(club_id, play_id)
        
        return user_number


class ClubBannerSerialize(serializers.ModelSerializer):
    """
    轮播图
    """

    class Meta:
        model = ClubBanner
        fields = ('active', 'image', 'banner_type', 'param', 'title')
