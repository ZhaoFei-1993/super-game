# -*- coding: UTF-8 -*-
from rest_framework import serializers
from datetime import datetime
from utils.functions import number_time_judgment
from utils.cache import get_cache, set_cache, delete_cache
from dragon_tiger.models import Dragontigerrecord
from chat.models import Club
from utils.functions import normalize_fraction


class RecordSerialize(serializers.ModelSerializer):
    """
    竞猜记录表序列化
    """
    bet = serializers.SerializerMethodField()  # 下注金额
    number_tab_number = serializers.SerializerMethodField()  # 牌局
    type = serializers.SerializerMethodField()  # 0.未开奖/1.答对/2.答错
    created_at = serializers.SerializerMethodField()  # 时间
    my_option = serializers.SerializerMethodField()  # 我的选项
    coin_avatar = serializers.SerializerMethodField()  # 货币图标
    coin_name = serializers.SerializerMethodField()  # 货币昵称
    earn_coin = serializers.SerializerMethodField()  # 竞猜结果
    is_right = serializers.SerializerMethodField()  # 是否为正确答案
    right_option = serializers.SerializerMethodField()  # 正确答案

    class Meta:
        model = Dragontigerrecord
        fields = ("id", "type", "number_tab_number", "bet", "created_at", "my_option", "coin_avatar", "coin_name",
                  "earn_coin", "is_right", "right_option")

    @staticmethod
    def get_bet(obj):  # 下注金额
        coin_accuracy = obj.club.coin.coin_accuracy
        bet = normalize_fraction(obj.bets, int(coin_accuracy))
        return bet

    @staticmethod
    def get_number_tab_number(obj):  # 牌局
        number_tab_number = obj.number_tab.number_tab_number
        return number_tab_number

    @staticmethod
    def get_type(obj):  # 0.未开奖/1.答对/2.答错
        if obj.earn_coin == 0 or obj.earn_coin == '':
            type = 0
        elif obj.earn_coin > 0:
            type = 1
        else:
            type = 2
        return type

    @staticmethod
    def get_created_at(obj):  # 时间
        years = obj.created_at.strftime('%Y')
        year = obj.created_at.strftime('%m/%d')
        time = obj.created_at.strftime('%H:%M')
        data = [{
            'years': years,
            'year': year,
            'time': time,
        }]
        return data

    @staticmethod
    def get_my_option(obj):  # 我的选项
        title = str(obj.option.title) + " - 1 ：" + str(int(obj.option.odds))
        return title

    @staticmethod
    def get_coin_avatar(obj):  # 货币图标
        coin_avatar = obj.club.coin.icon
        return coin_avatar

    @staticmethod
    def get_coin_name(obj):  # 货币昵称
        coin_name = obj.club.coin.name
        return coin_name

    def get_earn_coin(self, obj):  # 结果
        if obj.earn_coin == 0 or obj.earn_coin == '':
            earn_coin = "待开奖"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Wait results"
        elif obj.earn_coin < 0:
            earn_coin = "猜错"
            if self.context['request'].GET.get('language') == 'en':
                earn_coin = "Guess wrong"
        else:
            earn_coin = "+" + str(normalize_fraction(obj.earn_coin, int(obj.club.coin.coin_accuracy)))
        return earn_coin

    @staticmethod
    def get_right_option(obj):
        right_option = obj.number_tab.opening
        return right_option

    @staticmethod
    def get_is_right(obj):
        is_right = 0
        if obj.earn_coin > 0:
            is_right = 1
        elif obj.earn_coin < 0:
            is_right = 2
        return is_right