# -*- coding: UTF-8 -*-
from rest_framework import serializers
from users.models import User, Coin
from chat.models import Club
from quiz.models import Record
from base.validators import PhoneValidator


class ClubListSerialize(serializers.ModelSerializer):
    """
    序列号
    """
    coin_name = serializers.SerializerMethodField()  # 货币名称
    coin_key = serializers.SerializerMethodField()  # 货币ID
    user_number = serializers.SerializerMethodField()  # 总下注数
    coin_icon = serializers.SerializerMethodField()  # 货币头像

    class Meta:
        model = Club
        fields = ("id", "room_title", "autograph", "user_number", "room_number", "coin_name", "coin_key", "is_recommend"
                  , "icon", "coin_icon")

    @staticmethod
    def get_coin_name(obj):  # 货币名称
        coin_liat = Coin.objects.get(pk=obj.coin_id)
        coin_name = coin_liat.name
        return coin_name

    @staticmethod
    def get_coin_key(obj):  # 货币ID
        coin_list = Coin.objects.get(pk=obj.coin_id)
        coin_key = coin_list.pk
        return coin_key

    @staticmethod
    def get_user_number(obj):
        record_number = Record.objects.filter(roomquiz_id=obj.pk).count()
        if int(obj.is_recommend) == 0:
            record_number = 0
            return record_number
        elif int(obj.is_recommend) == 3:
            record_number += 10000
            return record_number
        elif int(obj.is_recommend) == 2:
            record_number += 6000
            return record_number
        elif int(obj.is_recommend) == 1:
            record_number += 4000
            return record_number

    @staticmethod
    def get_coin_icon(obj):  # 货币头像
        coin_liat = Coin.objects.get(pk=obj.coin_id)
        coin_icon = coin_liat.icon
        return coin_icon
