# -*- coding: UTF-8 -*-
from rest_framework import serializers
from chat.models import Club, ClubRule, ClubBanner
from users.models import User, Coin
from promotion.models import PromotionRecord


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


class RecordSerialize(serializers.ModelSerializer):
    """
    下注详细记录
    """
    user_info = serializers.SerializerMethodField()
    source_key = serializers.SerializerMethodField()
    coin_info = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()

    class Meta:
        model = PromotionRecord
        fields = ('user_info', 'source_key', 'status', 'record_id', 'source', 'earn_coin', 'bets', 'coin_info',
                  'created_at', 'source', 'time')

    def get_user_info(self, obj):
        """
        下注人信息
        """
        info = User.objects.get(id=obj.user_id)
        telephone = str(info.telephone)
        telephone = "+" + str(info.area_code) + " " + str(telephone[0:3]) + "***" + str(telephone[7:])
        user_info = {
            "user_id": info.id,
            "user_avatar": info.avatar,
            "user_telephone": telephone
        }
        return user_info

    def get_source_key(self, obj):
        """
        类型
        """
        source = PromotionRecord.SOURCE[int(obj.source)-1][1]
        return source

    def get_time(self, obj):
        """
        sjian
        """
        time = obj.open_prize_time.strftime('%H:%M:%S')
        yeas = obj.open_prize_time.strftime('%Y-%m-%d')
        created_ats = obj.open_prize_time.strftime('%Y-%m-%d %H:%M:%S')
        list = {
            "time": time,
            "yeas": yeas,
            "created_ats": created_ats,
        }
        return list

    def get_coin_info(self, obj):
        """
        货币信息
        """
        club_id = int(obj.club_id)
        club_info = Club.objects.get_one(pk=club_id)
        coin_info = Coin.objects.get_one(pk=int(club_info.coin_id))
        return coin_info
