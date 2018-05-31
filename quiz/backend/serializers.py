# -*- coding: UTF-8 -*-
from rest_framework import serializers
from django.utils import timezone
# from datetime import datetime

from ..models import Category, Record, Option, Quiz, OptionOdds
from chat.models import Club
from utils.functions import normalize_fraction


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    """
    竞猜分类
    """

    class Meta:
        model = Category
        fields = ("name", "parent", "is_delete")


class UserQuizSerializer(serializers.ModelSerializer):
    """
    用户竞猜记录
    """
    user_name = serializers.CharField(source='user.username')
    nick_name = serializers.CharField(source='user.nickname')
    # match_name = serializers.CharField(source='quiz.match_name')
    # host_team = serializers.CharField(source='quiz.host_team')
    # guest_team = serializers.CharField(source='quiz.guest_team')
    # coin_icon = serializers.CharField(source='coin.icon')
    # option = serializers.CharField(source='option.option')
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = (
            "user_name", "nick_name",  "odds", "bet", "earn_coin",
            "created_at")

    @staticmethod
    def get_created_at(obj):
        # create_time = timezone.localtime(obj.created_at)
        create_time = obj.created_at
        created = create_time.strftime("%Y-%m-%d %H:%M:%S")
        return created


class UserQuizListSerializer(serializers.ModelSerializer):
    """
    用户竞猜记录
    """
    coin_name = serializers.SerializerMethodField()
    category = serializers.CharField(source='quiz.category.parent.name')
    match_name = serializers.CharField(source='quiz.match_name')
    host_team = serializers.CharField(source='quiz.host_team')
    guest_team = serializers.CharField(source='quiz.guest_team')
    tips = serializers.CharField(source='rule.tips') #下注类型
    option = serializers.CharField(source='option.option.option') #下注选项
    estimate = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    begin_at = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()


    class Meta:
        model = Record
        fields = (
        'coin_name', 'category', 'match_name', 'host_team', 'guest_team', 'tips', 'option', 'odds', 'bet', 'estimate',
        'created_at', 'begin_at', 'result', 'earn_coin', 'status')

    @staticmethod
    def get_coin_name(obj):
        try:
            room = Club.objects.get(id=obj.roomquiz_id)
        except Exception:
            return ''
        coin_name = room.coin.name
        return coin_name


    @staticmethod
    def get_estimate(obj):
        result = obj.odds * obj.bet
        estimate=normalize_fraction(result, 8)
        return estimate

    @staticmethod
    def get_created_at(obj):
        create_time= obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return create_time

    @staticmethod
    def get_begin_at(obj):
        begin_time = obj.quiz.begin_at.strftime('%Y-%m-%d %H:%M:%S')
        return begin_time

    @staticmethod
    def get_result(obj):
        try:
            option = Option.objects.get(rule_id=obj.rule_id, is_right=1)
        except Exception:
            return ''
        return option.option


    @staticmethod
    def get_status(obj):
        for x in Quiz.STATUS_CHOICE:
            if int(obj.quiz.status)==x[0]:
                return x[1]
