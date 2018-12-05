# -*- coding: UTF-8 -*-
from rest_framework import serializers
from ..models import Club, ClubBanner, ClubRule
from users.models import Coin


class ClubBackendSerializer(serializers.ModelSerializer):
    coin_name = serializers.CharField(source='coin.name')
    created_at = serializers.SerializerMethodField()
    is_recommend = serializers.SerializerMethodField()

    class Meta:
        model = Club
        fields = ('id', 'room_title', 'autograph', 'icon', 'created_at', 'room_number', 'coin_name', 'is_recommend',
                  'is_dissolve', 'user', 'is_banker')

    @staticmethod
    def get_created_at(obj):
        create_time = obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return create_time

    @staticmethod
    def get_is_recommend(obj):
        choice = Club.STATUS_CHOICE
        for x in choice:
            if int(obj.is_recommend) == x[0]:
                recommend = x[1]
                return recommend


class BannerImageSerializer(serializers.ModelSerializer):
    """
    轮播图
    """
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = ClubBanner
        fields = ('id', 'image', 'active', 'order', 'is_delete', 'updated_at', 'language')

    @staticmethod
    def get_updated_at(obj):
        updated_at = obj.updated_at.strftime('%Y-%m-%d %H:%M')
        return updated_at


class ClubRuleBackendSerializer(serializers.ModelSerializer):
    """
    玩法序列化
    """
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = ClubRule
        fields = ('id', 'title', 'title_en', 'room_number', 'icon', 'sort', 'is_dissolve', 'is_deleted', 'created_at')

    @staticmethod
    def get_created_at(obj):
        created_at = obj.created_at.strftime('%Y-%m-%d %H:%M')
        return created_at


class CoinSerialize(serializers.ModelSerializer):
    """
    货币数据序列化
    """
    class Meta:
        model = Coin
        fields = ('id', 'name')
